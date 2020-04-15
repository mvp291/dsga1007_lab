#!/usr/bin/env python

'''Protocol:
S:Name?
C:<TEAM_NAME>
S:<player_id> <no_players> <no_types> <goal> <item_list>
#Example: 1 3 3 4 0 0 1 2 3 2 1 3 2 2 1
C:<bid>
S:<winner_id> <winner_bid> <player_budget>
.
.
.
'''

import socket
import sys
import threading
import time
import random
import Queue
import os
import pdb

def list_to_flat_string(l):
    result = ""
    for item in l:
        result += str(item) + " "
    return result[:-1]


class Server(object):

    """
    p is the number of players.

    k is the number of types
    n is the number that has to be achieved

    """

    def __init__(self, argport, argp, argk, argn, argr, argv):
        self.host = ''
        self.port = argport
        self.backlog = 5
        self.size = 1024
        self.eom = '<EOM>'
        self.server = None
        self.threads = []
        self.no_items = 10000

        #Game specific attributes
        self.p = argp
        self.k = argk
        self.n = argn
        self.r = argr
        self.v = argv
        self.item_list = [random.randint(0, k - 1)
                          for i in range(self.no_items)]
        #Matrix storing the owner; (i, j) = no.of items of type j player i owns
        self.item_owner = []
        for i in range(p):
            l = []
            for j in range(k):
                l.append(0)
            self.item_owner.append(l)


    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.settimeout(20)
            self.server.bind((self.host,self.port))
            self.server.listen(self.backlog)
        except socket.error, (value,message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        self.open_socket()
        i = 0
        while (1):
            if i == self.p:
                break
            player_id = len(self.threads)
            if player_id < self.r:
                c = RandomClient(player_id, 0, 10, 0, 2)
            else:
                try:
                    client, address = self.server.accept()
                except socket.timeout:
                    print "Client took too long to connect"
                    i += 1
                    continue
                #Do handshake
                client.send("Name?" + self.eom)
                try:
                    name = client.recv(self.size).strip()
                except socket.timeout:
                    print "Client took too long to send name"
                    i += 1
                    continue
                greeting = [player_id, self.p, self.k, self.n] + self.item_list
                client.send(list_to_flat_string(greeting) + self.eom)
                c = Client((client, address), player_id, name, 120000)
            c.start()
            self.threads.append(c)
            i += 1
        #Accept no more incoming connections
        self.server.close()
        #Visualizer
        if self.v:
            self.visualizer = Visualizer(self.n,
                                         [(client.name, client.time)
                                          for client in self.threads if client.is_alive()],
                                         self.item_list)

        for i in range(len(self.item_list)):
            item = self.item_list[i]
            alive_clients = [client for client in self.threads if client.is_alive()]
            #Receive bid
            round_start_time = time.time()
            for client in alive_clients:
                client.out_msg_queue.get(block=True)
            highest_bid = max([client.bid for client in alive_clients])
            highest_bidder = [client for client in alive_clients if client.bid == highest_bid]
            #If two player have the same bid and timestamp, the winner is chosen uniformly random
            lowest_time = min(highest_bidder, key=lambda x: x.time)
            fastest_winner = [client for client in highest_bidder if client.time == lowest_time.time]
            winner = fastest_winner[random.randint(0, (len(fastest_winner) - 1))]
#Insert time.time() were appropiate and send difference via client.time to update
#Make sure to use max(diff, 0) to not send negative values!
#Sven works in seconds, so divide it by 1000.0 (if accepting floats, 1000 otherwise)
#Make CSV file with "command", "parakeet", "strategy name", "image file"
            if self.v:
                for client in alive_clients:
                    self.visualizer.update(client.player_id,
                                           client.bid,
                                           max(client.bid_time - round_start_time, 0))
                    time.sleep(0.5)
                self.visualizer.update(winner.player_id, -1)
                time.sleep(1)
            print "{0} - Player {1} wins item {2} for {3}.".format(i,winner.name, item, winner.bid)
            self.item_owner[winner.player_id][item] += 1
            for client in alive_clients:
            #print " pid: " + str(client.player_id) + ", b: " + str(client.budget) + ", bid: " + str(client.bid)
                client.inc_msg_queue.put([winner.player_id, winner.bid], block=True)
            if self.item_owner[winner.player_id][item] == self.n:
                print "Player " + str(winner.name) + " won the game."
                break

        #Close all threads
        for c in [client for client in self.threads if client.is_alive()]:
            c.inc_msg_queue.put(0)

class RandomClient(threading.Thread):

    def __init__(self,player_id, bid_low, bid_high, wait_low, wait_high):
        threading.Thread.__init__(self)
        #Game specific attributes
        self.budget = 100
        self.player_id = player_id
        self.name = "Random" + str(self.player_id)
        #The bidding system
        self.bid = 0
        self.bid_time = sys.float_info.max
        self.out_msg_queue = Queue.Queue(maxsize=1)
        self.inc_msg_queue = Queue.Queue(maxsize=1)

        #Controls the number of ms per player
        self.time = 120000

        #How long to wait after generating a bid
        self.wait_low = wait_low
        self.wait_high = wait_high

        self.bid_low = bid_low
        self.bid_high = bid_high

    def run(self):
        while (1):
            before = time.time()
            bid = random.randint(self.bid_low, self.bid_high)
            time.sleep(0.1 * random.randint(self.wait_low, self.wait_high))
            after = time.time()
            self.time -= after - before
            if self.time <= 0:
                print "Player {0} timed out and is disqualified.".format(self.name)
                self.running = 0
                break
            if bid > self.budget:
                self.bid = 0
            else:
                self.bid = bid
            #If I bid ealier than my competitor I'd win
            self.bid_time = time.time()
            #Now I want to communicate my bid and receive the result
            self.out_msg_queue.put(bid)
            #The parent has entered the information and I can continue
            inc = self.inc_msg_queue.get(block=True)
            if inc:
                [winner_id, winner_bid] = inc
                if self.player_id == winner_id:
                    self.budget -= self.bid
            else:
                break
        self.out_msg_queue.put(-1)

class Client(threading.Thread):

    def __init__(self,(client,address), player_id, name, time):
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
        self.time = time
        self.client.settimeout(self.time)
        self.running = 1

    def run(self):
        while (self.running):
            before = time.time()
            bid = self.client.recv(self.size)
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
            inc = self.inc_msg_queue.get(block=True)
            if inc:
                [winner_id, winner_bid] = inc
                if self.player_id == winner_id:
                    self.budget -= self.bid
                self.client.send(list_to_flat_string([winner_id, winner_bid, self.budget]) + self.eom)
            else:
                self.client.close()
                break
        #Something bad happened, but the server is still expecting us to deliver, so
        #we just answer with a bid that cannot possibly win
        self.out_msg_queue.put(-1, block=True)

if __name__ == "__main__":
    if len(sys.argv) != 8:
        print "Usage: " + sys.argv[0] + " port p k n seed r v"
    else:
        try:
            [port, p, k, n, seed, r, v] = map(int, sys.argv[1:])
        except ValueError:
            print "Arguments have to be all integers"
            sys.exit(0)
        if seed:
            random.seed(seed)
        if r > p:
            print "Cannot have more random players than players"
            sys.exit(0)
        if v:
            from basic_visualizer import Visualizer
        s = Server(port, p, k, n, r, v)
        s.run()
        os._exit(0)


