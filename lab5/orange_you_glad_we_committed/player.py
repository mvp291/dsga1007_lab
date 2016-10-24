'''
Created on Nov 14, 2013

@author: tom
'''

import numpy as np
import sys
import time
import random
import socket

MONEY=100

class Player:
    def __init__(self,pid,P,K,N,items,strategy,params,verbose=True,sleep=-1):
        # Set overall parameters
        self.pid=pid
        self.P  =P
        self.K  =K
        self.N  =N
        self.strategy=strategy
        self.params = params
        self.v=verbose
        self.sleep=sleep
        self.maxGameLen=P*K*(N-1)+1
        self.itemList=np.array(items[:self.maxGameLen],dtype='int')
        self.itemsSoFar=np.zeros((self.maxGameLen,self.K),dtype='int')
        if self.v: print "INITIALIZED with playerid=%d, P=%d, K=%d, N=%d"%(pid,P,K,N)
        # check some basics
        assert(self.pid<self.P)
        assert(np.array_equal(np.unique(self.itemList), np.arange(self.K)))
        # Generate game status arrays
        self.playeritems = np.zeros((self.P,self.K))
        self.playerbudgets = np.ones((self.P,))*MONEY
        self.myItems=self.playeritems[self.pid]
        self.myBudget=self.playerbudgets[self.pid]
        self.m = 0 # move counter
        self.winningid=-1
        # Generate overview variables
        self.roundsToWin=np.zeros((self.P,self.K),dtype='int')
        self.itemsToWin =np.ones ((self.P,self.K),dtype='int')*self.N
        self.valuation  =np.zeros((self.P,self.K)) # has to be updated through algorithm
        self.myValuation=np.zeros((self.K,))
        self.danger     =np.zeros((self.P,self.K)) #budget / itemsToWin * timefactor()
        # 1) build itemsSoFar
        for m,k in enumerate(self.itemList[:1000]):
            self.itemsSoFar[m:,k]+=1
        # 2) build roundsToWin: will be the same for each player
        rtw=[np.searchsorted(self.itemsSoFar[:,k],self.N) for k in xrange(self.K)]
        for p in xrange(self.P): self.roundsToWin[p,:]=rtw # fill up nparray
        self.calcSimpleValuation()
        # Strategy parameters
        if self.strategy=='exp':
            self.expA=None
            self.expB=None
            self.expWanted=None
            self.set_exp_strategy()
    
    def updateOverview(self,wonid,wonbid):
        currItem=self.itemList[self.m]
        self.itemsToWin[wonid,currItem]-=1
        # update RTW: 
        for k in xrange(self.K):
            if k==currItem:
                # update current item rtw: different for each player
                for p in xrange(self.P):
                    if p==wonid:
                        self.roundsToWin[p,k]-=1
                        # TODO remove expensive line
                        assert(self.roundsToWin[p,k]==np.searchsorted(self.itemsSoFar[self.m+1:,k], self.itemsToWin[p,k]))+1
                    else:
                        self.roundsToWin[p,k]=np.searchsorted(self.itemsSoFar[self.m+1:,k], self.itemsSoFar[self.m,k]+self.itemsToWin[p,k])
            else:
                self.roundsToWin[:,k]-=1
        # update danger
#         firstwin=np.min(self.roundsToWin)
        
#         self.danger=
    
    def update(self, update):
        wonid,wonbid,mymoney=[int(v) for v in update.split(' ')]
        currItem=self.itemList[self.m]
        self.playeritems[wonid,currItem]+=1
        self.playerbudgets[wonid] -= wonbid
        if wonid==self.pid:
            self.myItems=self.playeritems[self.pid]
            self.myBudget=self.playerbudgets[self.pid]
            if self.v: print "I won bid. my budget=%d / my items=[%s]" % (self.myBudget, ','.join(['%d:%d'%(k,val) for k,val in enumerate(self.myItems)]))
        assert(self.myBudget==mymoney)
        # Check if this was game-winning bid
        if self.playeritems[wonid,currItem]==self.N:
            self.winningid=wonid
            if wonid!=self.pid:
                if self.v: print "Player %d won the game with %d items of k=%d"%(wonid,self.N, currItem)
            else:
                if self.v: print "HURRAY I WON THE GAME!!! Pid=%d won the game with %d items of k=%d"%(wonid,self.N, currItem)
        else:
            self.updateOverview(wonid,wonbid)
            if self.v: print "Player %d won bid (item %d) for %d units, his leftover budget is %d"%(wonid,currItem,wonbid,self.playerbudgets[wonid])
            self.m+=1            
        
    def calcSimpleValuation(self):
        for p in xrange(self.P):
            for k in xrange(self.K):
                timefac=1.*(np.min(self.roundsToWin[p,:])+1)/(self.roundsToWin[p,k]+1) # <=1 
                itemfac=1./self.itemsToWin[p,k]
                self.valuation[p,k] = timefac*itemfac*self.playerbudgets[p]
#                 self.myValuation[k] = 2/(self.N-self.itemsToWin[self.pid,k]+self.roundsToWin[self.pid,k])*self.myBudget  
    def play_param_mult (self):
        item=self.itemList[self.m]
        # baserate
        val=self.params[0]*float(self.myItems[item]+1)/(0.3*self.K*self.N)
        # multiplicative with parameters as base, score as exponent
        scores=self.collect_scores()
        out="Valuation multiplicative = %.2f "%val
        for par,sc in zip(self.params[1:], scores):
            val*=(1+par)**sc
            out+="* (1+%.4f)^%.1f " %(par,sc)
        if self.v: print out+" = %.4f"%val
        if val>=1:
            if self.v: print "param_mult  unexpected high valuation val=%.4f"%val
            val=1
        return int(val*self.myBudget)
    
    def play_param_add(self):
        # additive with parameters as prefactor, score as factor
        item=self.itemList[self.m]
        # baserate
        val=self.params[0]*float(self.myItems[item]+1)/(0.3*self.K*self.N)
        # multiplicative with parameters as base, score as exponent
        scores=self.collect_scores()
        out="%d - Valuation additive = %.4f "%(self.m,val)
        for par,sc in zip(self.params[1:], scores):
            val+=par/(self.K*self.N)*sc
            out+="+ %.4f*%.1f " %(par/(self.K*self.N),sc)
        if self.v: print out+" = %.4f"%val
        ## Other ideas: competition based on other players number of this item.
        if val>=1:
            if self.v: print "param_add  unexpected high valuation val=%.4f"%val
            val=1
        elif val<0:
            if self.v: print "param_add  unexpected negative valuation val=%.4f"%val
            val=0
        return val*self.myBudget
    
    def collect_scores(self):
        b=self.score_rtw()
        c=self.score_lockdown()
        d=self.score_takeover()
        e=self.score_lockd2()
        return (b,c,d,e)
    
    def score_rtw(self):
        # Returns score for how nearby the closest win is. Normalization based on negative binomial distribution
        # with failure=drawing correct class, success=drawing anything else. r=N  
        # NOT IN 0 1 range!!  
        item=self.itemList[self.m]
        return float(self.K*self.N) / np.max((self.roundsToWin[self.pid,item]+1),0.1) # no division by zero this time!
    
    def score_lockdown(self):
        item = self.itemList[self.m]
        #Get the closest I am to winning on some other item
        #If I am already really close to winning on something else, don't bother locking down on this one
        #But, this doesn't take into account how many rounds are left to winning- leave it to genetics
        closest = min(self.itemsToWin[self.pid])
        if (float(closest)/self.N<=0.6 and self.itemsToWin[self.pid,item]!=closest):
            return -1
        return 0
    
    def score_lockd2(self):
        item = self.itemList[self.m]
        # Lockdown if I am above a certain threshold
        ldthreshold = 0.4
        fraction_acquired = float(self.myItems[item])/self.N
        if (fraction_acquired>=ldthreshold):
            return 1
        
        # Otherwise, I am indifferent
        return 0
    
    def score_takeover(self):
        item = self.itemList[self.m]
        # if opponent has many <=N-3 of this type but low budget: +1
        tothreshold = 3
        bpthreshold = float(self.playerbudgets[self.pid])/min(self.itemsToWin[self.pid,:])
        rtwthreshold = self.N/self.K #shouldn't this also depend on K? 
        
        potentialprey = np.where(self.itemsToWin[:,item]<=tothreshold)[0]
        if potentialprey.size==1:
            ppid = potentialprey[0]
            buyingpower = float(self.playerbudgets[ppid])/self.itemsToWin[ppid][item]
            if ( buyingpower < 0.8*bpthreshold and 
                float(min(self.roundsToWin[self.pid,:]))/self.roundsToWin[self.pid][item] < rtwthreshold):
                    return 1
                
        # Same as in score lockdown
        closest = min(self.itemsToWin[self.pid])
        if (float(closest)/self.N<=0.3 and self.itemsToWin[self.pid][item]!=closest):
            return -1
        
        return 0
    
    
    def set_exp_strategy(self):
        a = 3. #need to improve
        b = 10.
        bidsum=101
        while (bidsum>100-1.5*self.K*a):
            b*=0.9
            bidsum=np.sum([int(a*(b**n)) for n in xrange(self.N)])
        self.expA = a
        self.expB = b
        self.expWanted=np.random.randint(0,self.K)
        if self.v: print "Set exponential strategy, A=%d, B=%d (sums to %d). I will go after item %d"%(a,b,bidsum,self.expWanted)
        
        
    def play_exp(self):
        # update wanted item for exponential bidder
        topk=np.argmax(self.myItems)
        topn=np.max(self.myItems) # 
        if topn>0 and self.expWanted!=topk and topn>self.myItems[self.expWanted]:
            self.expWanted=topk
        n=self.myItems[self.expWanted] # how much we currently have
        # if this is the WANTED item, bid exponentially
        curItem=self.itemList[self.m]
        if (curItem==self.expWanted):
            bid = int(self.expA*(self.expB ** n))
        else:
            bid= int(self.expA)
        return bid
    
    def play_simple(self):
        self.calcSimpleValuation()
        currItem=self.itemList[self.m]
        bid= min(self.myBudget, int(self.valuation[self.pid,currItem]))
        if self.v: print "In play_simple: bidding %d, myBudget=%d and valuation=%d" % (bid,self.myBudget , int(self.valuation[self.pid,currItem]))
        return bid

    def update_lazy(self):    
        return self
    
    def play(self):
        blockthreshold = 30 #Need to update genetically?
        
        item=self.itemList[self.m]
        if self.itemsToWin[self.pid][item] == 1:
            if self.v: print "%d - last item, bid maximum %d"%(self.m, self.playerbudgets[self.pid])
            return self.playerbudgets[self.pid]
        
        dangerplayers=np.where(self.itemsToWin[:,item]==1)[0]
        max = 0
        for i in dangerplayers:
            if self.playerbudgets[i] > max:
                max = self.playerbudgets[i]
                mostDangerous = i
        if max>0 and self.v: print "%d - detected dangerous players: %s with budget %d"%(self.m,str(dangerplayers), self.playerbudgets[mostDangerous])
        if max!=0 and max < blockthreshold and self.myBudget>1.5*max:
            bid = max+1
            if self.sleep>0:
                time.sleep(self.sleep)
            elif self.sleep<0:
                time.sleep(np.random.rand())
            elif self.sleep==0:
                pass
            return min(self.myBudget,bid)
        
        # Not N-1 situation: normal valuation
        if self.v: print "Playing with strategy %s"%self.strategy
        if self.strategy=='exp':
            return self.play_exp()
        elif self.strategy=='simple':
            return self.play_simple()
        elif self.strategy=='param_add':
            return self.play_param_add()
        elif self.strategy=='param_mult':
            return self.play_param_mult()
        
def receive():
    global s
    msg = ''
    while '<EOM>' not in msg:
        chunk = s.recv(1024)
        if not chunk: break
        if chunk == '':
            raise RuntimeError("socket connection broken")
        msg += chunk
    msg = msg[:-5]
    return msg

def send(msg):
    global s, P
#     print "Round %d, msg: %s"%(P.m,msg)
    s.send(msg)

if __name__ == "__main__":
    # Parse cl args
    port=int(sys.argv[1])
    name='Brie'
    strategy='simple'  # exp, simple, param_add, param_mult
    params=[]
    if len(sys.argv)>=3: name=sys.argv[2]
    if len(sys.argv)>=4: strategy=sys.argv[3]
    if len(sys.argv)>=5: params=[float(v) for v in sys.argv[4:]]
    # connect and initialize
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    assert( receive()=='Name?') 
    s.send(name)
    info=[int(v) for v in receive().split(' ')]
    
    print "Initializing player with strategy %s and params %s" % (strategy, str(params))
    P=Player(info[0], info[1], info[2], info[3], info[4:], strategy, params)
    while (P.winningid<0):
        bid=P.play()
        print "%d - I bid %d / %d in round %d, item k=%d"%(P.m, bid,P.myBudget,P.m, P.itemList[P.m])
        send('%d'%int(bid))
        upd=receive()
        P.update(upd)
    print "GAME OVER"
    time.sleep(1) # not to get the disqualified msg immediately
    s.close()
    if P.winningid==P.pid:
        sys.exit(0) # won
    else:
        sys.exit(1) # lost
        
        

