#!/usr/bin/env python

'''Protocol: 
S:Name?
C:<TEAM_NAME>
S:<player_id> <no_players> <no_types> <goal> <item_list> #Example: 1 3 3 4 0 0 1 2 3 2 1 3 2 2 1
C:<bid>
S:<winner_id> <winner_bid> <player_budget>
.
.
.
S:sends nothing (don't know why, but for now considered feature)
'''

import select
import socket
import sys
import threading
import time
import pdb
import random
import Queue

def list_to_flat_string(l):
    result = ""
    for item in l:
        result += str(item) + " "
    return result[:-1]

class Server:
    '''p is the number of players
    k is the number of types
    n is the number that has to be achieved'''
    def __init__(self, port, p, k, n):
        self.host = ''
        self.port = port
        self.backlog = 5
        self.size = 1024
        self.eom = '<EOM>'
        self.server = None
        self.threads = []
        self.no_items = 1000
       
        #Game specific attributes
        self.p = p
        self.k = k 
        self.n = n
        self.item_list = map(lambda x: random.randint(0, k - 1), range(self.no_items))
        #Matrix storing the owner; (i, j) = no. of items of type j player i owns 
        self.item_owner = p*[k*[0]]
       
    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host,self.port))
            self.server.listen(self.backlog)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        self.open_socket()
        while (len(self.threads) < self.p):
            player_id = len(self.threads)
            client, address = self.server.accept()
            #Do handshake
            client.send("Name?" + self.eom)
            name = client.recv(self.size).strip()
            greeting = [player_id, self.p, self.k, self.n] + self.item_list 
            client.send(list_to_flat_string(greeting) + self.eom)
            c = Client((client, address), player_id, name)
            c.start()
            self.threads.append(c)

        for item in self.item_list:
            alive_clients = [client for client in self.threads if client.is_alive()]
            #Wait for the clients to receive their bids
            highest_bid = max(alive_clients, key=lambda x: x.out_msg_queue.get(block=True))
            highest_bidder = [client for client in alive_clients if client.bid == highest_bid.bid]
            #If two player have the same bid and timestamp, the winner is chosen uniformly random
            lowest_time = min(highest_bidder, key=lambda x: x.time)
            fastest_winner = [client for client in highest_bidder if client.time == lowest_time.time]
            winner = fastest_winner[random.randint(0, (len(fastest_winner) - 1))]
            print "Player {0} wins item {1} for {2}.".format(winner.name, item, winner.bid)
            self.item_owner[winner.player_id][item] += 1
            if self.item_owner[winner.player_id][item] == self.n:
            	print "Player " + str(winner.name) + " won the game."
            	break
            for client in alive_clients:
                client.inc_msg_queue.put([winner.player_id, winner.bid], block=True)
 
        #Close all threads
        self.server.close()
        for c in self.threads:
            c.join()

class Client(threading.Thread):

    def __init__(self,(client,address), player_id, name):
        threading.Thread.__init__(self)
        self.size = 1024
        self.eom = '<EOM>'
        self.client = client
        self.address = address
        #Game specific attributes
        self.budget = 100
        self.player_id = player_id
        self.name = name
        #The bidding system
        self.bid = 0
        self.bid_time = sys.float_info.max
        self.out_msg_queue = Queue.Queue(maxsize=1)
        self.inc_msg_queue = Queue.Queue(maxsize=1)
       
        #Controls the number of ms per player 
        self.time = 120000
        self.client.settimeout(self.time)
        self.running = 1

    def run(self):
        while (self.running):
            before = time.time()
            bid = str(self.client.recv(self.size))
            after = time.time()
            self.time -= after - before
            if self.time <= 0:
                print "Player {0} timed out and is disqualified.".format(self.name)
                self.client.close()
                self.running = 0
                break
            if bid:
                try:
                    bid = int(bid)
                except ValueError:
                    print ("Player {0} sent invalid bid: {1}" 
                                        "and is disqualified.").format(self.name, self.bid)
                    self.client.close()
                    self.running = 0
                    break
                if bid > self.budget:
                    self.bid = 0
                else:
                    self.bid = bid
            else:
                self.client.close()
                self.running = 0
                print "Player {0} disconnected and is disqualified.".format(self.name)
                break
            #If I bid ealier than my competitor I'd win
            self.bid_time = time.time()
            #Now I want to communicate my bid and receive the result
            self.out_msg_queue.put(bid, block=True)
            #The parent has entered the information and I can continue
            [winner_id, winner_bid] = self.inc_msg_queue.get(block=True)
            if self.player_id == winner_id:
                self.budget -= self.bid
            self.client.send(list_to_flat_string([winner_id, winner_bid, self.budget]) + self.eom)
        self.client.close()

    def join(self, timeout=None):
        self.running = 0
        super(Client, self).join(timeout)

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print "Usage: " + sys.argv[0] + " port p k n seed"
    else:
        try:
            [port, p, k, n, seed] = map(int, sys.argv[1:])
        except ValueError:
            print "Arguments have to be all integers"
            sys.exit(0)
        random.seed(seed)
        s = Server(port, p, k, n)
        s.run()


