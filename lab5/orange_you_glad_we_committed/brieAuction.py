'''
Created on Nov 19, 2013

@author: tom
'''

import player
import socket
import sys
import numpy as np
import random
import time

tic=time.time()
# np.random.seed(189347)
MONEY=100
budgets=None
items=None

def playgame(cands):
    global P,K,N,itemList, budgets,items
    assert(len(cands)==P)
    # initalize players from candidates
    players=[]
    for pid,cand in enumerate(cands):
        #pid, P,K,N,items,strategy,params
        players.append(player.Player(pid, P,K,N,itemList, cand['strategy'], cand['params'], False, 0))
    # play rounds with these players. check invalid bids, random selection if same bid
    budgets=[MONEY for pid in range(len(players))]
    items=np.zeros((P,K),dtype='int')
    for item in itemList:
        bids=[int(pl.play()) for pl in players]
        for pid,bid in enumerate(bids):
            if bid>players[pid].myBudget:
                raise Exception('Invalid bid, pid=%d bid=%d budget=%d'%(pid,bid)) # todo replace by warning
                bids[pid]=0
        winbid=np.max(bids)
        winners=np.where(bids==winbid)[0]
        winner=random.choice(winners)
        budgets[winner]-=winbid
        items[winner,item]+=1
        # update players: wonid,wonbid,mymoney
        for pid,pl in enumerate(players):
            pl.update('%d %d %d'%(winner,winbid,budgets[pid]))
        if items[winner,item]==N:
            assert(players[0].winningid==winner)
            break
    # Update plays and wins of each candidate
    cands[winner]['wins']+=1
#     for cand in cands: cand['plays']+=1

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
    global s, pl
#     print "Round %d, msg: %s"%(pl.m,msg)
    s.send(msg)

#===============================================================================
# Initialize game from server 
#===============================================================================
port=int(sys.argv[1])
name='Brie'
strategy='param_add'
if len(sys.argv)>=3: name=sys.argv[2]
if len(sys.argv)>=4: strategy=sys.argv[3]
# connect and initialize
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', port))
assert( receive()=='Name?') 
s.send(name)
info=[int(v) for v in receive().split(' ')]
PID,P,K,N,itemList=info[0], info[1], info[2], info[3], info[4:]
print "Search parameter space for P=%d, K=%d, N=%d" % (P,K,N)

try:
    #===============================================================================
    # Random Search
    #===============================================================================
    # pmaxes=np.array([2.0, 0.5, 0.5, 0.5])
    # numcands=200
    # rparams=[np.random.rand(pmaxes.size)*pmaxes for n in range(numcands)]
    # candidates=[{'strategy':'param_add', 'params':p,'plays':0,'wins':0} for p in rparams]
    
    #===============================================================================
    # Make pool and play games
    #===============================================================================
    if P>=7:
        Ngames=5
        timelim=60
    else:
        Ngames=7
        timelim=90
    pmaxes=np.array([1.0, 1.0, 1.0, 1.0,1.6])
    #==========================================================================
    # Generate init population
    #==========================================================================
    numcands=int(round(200/(P-2))*(P-2))
    print "Generate initial population with %d candidates" % numcands
    rparams=[np.random.rand(pmaxes.size)*pmaxes for n in range(numcands)]
    candidates=[{'strategy':strategy, 'params':p,'plays':0,'wins':0} for p in rparams]
    candsimple={'strategy':'simple','params':[],'plays':0,'wins':0}
    candbaseline={'strategy':'param_add','params':[0.5,0.,0.,0.,0.],'plays':0,'wins':0}
    
    generation=0
    print ("Generation %d -- Playing  pool of  %d candidates in %d games: round " % (generation, numcands, numcands/(P-2))),
    for j in range(Ngames):
        np.random.shuffle(candidates)
        print (" %d "%j),
        for i in range(0,numcands,P-2):
            cands=candidates[i:i+P-2]
            cands.append(candsimple)
            cands.append(candbaseline)
            playgame(cands)
    print " STOP."
    while (time.time()-tic<timelim):
        print "Timecheck: %.1f sec"%(time.time()-tic)
        generation+=1
        #===========================================================================
        # Select fittest candidates
        #===========================================================================
        wins=np.array([c['wins'] for c in candidates])
        maxwins=np.max(wins)
        parent_thr=maxwins+1
        nparents=0
        while (nparents<=0.10*numcands and parent_thr>=2):
            parent_thr-=1
            parents=[c for c in candidates if c['wins']>=parent_thr]
            nparents=len(parents)
        for p in parents:  p['wins']=0
        print "Generation %d -- Selected %d parents who won >= %d out of %d" % (generation,nparents, parent_thr, Ngames) 
        #===========================================================================
        # Make babies
        #===========================================================================
        mutants=np.random.randint(int(0.05*numcands))
        print "Generation %d -- Make %d babies of which %d mutants" % (generation,numcands-nparents , mutants)
        candidates=parents[:] # copy list
        while (len(candidates)<numcands):
            mom,dad=random.sample(parents,2)
            params=mom['params']
            ndadparams=np.random.randint(1,len(params))
            dadparams=random.sample(range(len(params)), ndadparams)
            for dadp in dadparams: params[dadp]=dad['params'][dadp]
            baby={'strategy':strategy, 'params':params,'plays':0,'wins':0} 
            candidates.append(baby)
        # mutations: change some parameters with +-50%
        for mutant in random.sample(candidates[nparents:],mutants):
            n_mutparams=np.random.randint(len(mutant['params']))
            mutparams=random.sample(range(len(params)), n_mutparams)
            for i in mutparams: mutant['params'][i]*=np.random.rand()+0.5
        print ("Generation %d -- Playing  pool of  %d candidates in %d games: round " % (generation, numcands, numcands/(P-2))),
        for j in range(Ngames):
            np.random.shuffle(candidates)
            print (" %d "%j),
            for i in range(0,numcands,P-2):
                cands=candidates[i:i+P-2]
                cands.append(candsimple)
                cands.append(candbaseline)
                playgame(cands)
        print " STOP."
    
    wins=[c['wins'] for c in candidates]
    maxwins=np.max(wins)
    wincands=np.where(wins==maxwins)[0]
    print "Selected %d candidates that won %d out of %d"%(wincands.size,maxwins,Ngames)
    print "Params: %s" % str([candidates[i]['params'] for i in wincands])
    wincand=random.choice(wincands)
    beststrategy=candidates[wincand]['strategy']
    bestparams=candidates[wincand]['params']
    print ("Selecting top performers")
    Ngames+=numcands/P
    
    print "Finished playing %d games"%Ngames
except Exception as e:
    print "EXCEPTION in genetic algorithm, fall back to sensible defaults"
    beststrategy=strategy
    bestparams=[0.3, 0.15, 0.1, 0.6, 0.8]

#===============================================================================
# Real game
#===============================================================================
print "Initializing player with strategy %s and params %s" % (beststrategy, str(bestparams))
pl=player.Player(PID, P,K,N,itemList, beststrategy, bestparams, True, 1.0)
while (pl.winningid<0):
    bid=pl.play()
    print "%d - I bid %d / %d in round %d, item k=%d"%(pl.m, bid,pl.myBudget,pl.m, pl.itemList[pl.m])
    send('%d'%int(bid))
    upd=receive()
    pl.update(upd)
print "GAME OVER"
time.sleep(1)
s.close()

