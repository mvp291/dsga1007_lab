from Tkinter import *
import random
from sets import Set
import operator
import time


class Visualizer():

    class Player():
        def __init__(self, teamid, teamname, money, time):
            self.teamid = teamid
            self.teamname = teamname
            self.money = money
            self.time = time

            self.current_bid = 0

            self.items = {}

        def update(self, bid, time_used, item_won=-1):
            if item_won != -1:
                self.money = max(self.money - self.current_bid, 0)
                if item_won in self.items:
                    self.items[item_won] = self.items.get(item_won) + 1
                else:
                    self.items[item_won] = 1

            self.time = max(self.time - time_used, 0)
            self.current_bid = bid

    # The Player Class

    def __init__(self, goal, team_list, itemlist, init_money=100):
        self.goal = goal
        self.players = []
        self.pot_item_names = ['Balisto', 'Daim', 'Excellence', 'Flake', 'Godiva',
                               'Hay Hay', 'Idaho Spud', 'KitKat', 'Lion', 'Mars',
                               'Noisette', 'Oreo', 'Penguin', 'Rolo', 'Snickers',
                               'Twix', 'UnoBar', 'Valomilk', 'WunderBar', 'Yorkie',
                               'Zero Bar']

        self.item_names = ['Almond Joy', 'Caramello Koala']
        self.item_colors = ['red', 'blue', 'magenta', 'purple', 'grey', 'darkblue', 'brown',
                            'violet', 'darkgreen', 'orange']

        random.shuffle(self.item_colors)

        self.itemlist = itemlist[:]
        random.shuffle(self.pot_item_names)
            # Create all Player instances
        for i in range(0, len(team_list)):
            teamid = i
            name = team_list[i][0]
            money = init_money
            time = int(team_list[i][1])

            new_player = self.Player(teamid, name, money, time)
            self.players.append(new_player)

        # Create item names
        self.diff_items = len(Set(itemlist))
        for i in range(int(self.diff_items) - 2):  # -2 because almond and caramel are always in
            self.item_names.append(self.pot_item_names.pop())

        self.item_names.sort()

        print self.item_names


        # Current item
        self.current_item = self.itemlist.pop(0)
        self.last_item = -1
        self.last_winner = -1

        self.master = Tk()

        # Height is dependent on number of players
        self.w = Canvas(self.master, width=550, height=70 * len(self.players) + 10 * len(self.players) + 140)
        self.w.pack()

        self.draw_scoreboard()


    def draw_scoreboard(self,end=-1):
        self.w.delete("all")
        x_offset = 10
        y_offset = 10

        # draw status
        text_in = 'Current item:'
        self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
        x_offset += len(text_in) * 6 + 20
        item = self.item_names[self.current_item]
        self.w.create_oval((x_offset, y_offset + 1, x_offset + 12, y_offset + 3 + 10), fill=self.item_colors[self.current_item])
        self.w.create_text((x_offset + 2, y_offset), text=item[0], justify='left', anchor='nw')
        x_offset += 15
        self.w.create_text((x_offset, y_offset), text=item, justify='left', anchor='nw', fill=self.item_colors[self.current_item])
        x_offset += len(item) * 6 + 20
        text_in = 'Last item:'
        self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
        x_offset += len(text_in) * 6 + 5
        if(self.last_item > -1):
            item = self.item_names[self.last_item]
            self.w.create_oval((x_offset, y_offset + 1, x_offset + 12, y_offset + 3 + 10), fill=self.item_colors[self.last_item])
            self.w.create_text((x_offset + 2, y_offset), text=item[0], justify='left', anchor='nw')
            x_offset += 15
            self.w.create_text((x_offset, y_offset), text=item, justify='left', anchor='nw', fill=self.item_colors[self.last_item])
            x_offset += len(item) * 6 + 20
        text_in = 'Last Winner:'
        self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
        x_offset += len(text_in) * 6 + 10
        if(self.last_winner > -1):
            self.w.create_text((x_offset, y_offset), text=self.last_winner, justify='left', anchor='nw')
        x_offset = 10
        y_offset += 30
        text_in = 'Next ' + str(min(int(self.goal), len(self.itemlist))) + ' items:'
        self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
        x_offset += len(text_in) * 6 + 20
        for i in range(min(int(self.goal), len(self.itemlist))):
            item = self.item_names[self.itemlist[i]]
            self.w.create_oval((x_offset, y_offset + 1, x_offset + 12, y_offset + 10 + 3), fill=self.item_colors[self.itemlist[i]])
            self.w.create_text((x_offset + 2, y_offset), text=item[0], justify='left', anchor='nw')
            x_offset += 15
            self.w.create_text((x_offset, y_offset), text=item, justify='left', anchor='nw', fill=self.item_colors[self.itemlist[i]])
            x_offset += len(item) * 6 + 20

        y_offset += 27

        self.w.create_line(0, y_offset, 600, y_offset)

        y_offset += 27

        for player in self.players:
            x_offset = 30
            text_in = player.teamname + ":"
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw', fill='red')
            x_offset = 100
            text_in = 'Items:'
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            x_offset += len(text_in) * 6 + 20
            for (key, value) in sorted(player.items.iteritems(), key=operator.itemgetter(1), reverse=True):
                text_in = str(value) + "* "
                self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
                x_offset += len(text_in) * 6
                item = self.item_names[key]
                self.w.create_oval((x_offset, y_offset + 1, x_offset + 12, y_offset + 10 + 3), fill=self.item_colors[key])
                self.w.create_text((x_offset + 1, y_offset), text=item[0], justify='left', anchor='nw')
                x_offset += 15
                self.w.create_text((x_offset, y_offset), text=item, justify='left', anchor='nw')
                x_offset += len(item) * 6 + 20
            x_offset = 100
            y_offset += 35
            if(player.teamid == end):
                text_in = 'WINNER'
                self.w.create_text((30, y_offset), text=text_in, justify='left', anchor='nw')
            text_in = 'Current Bid:'
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            x_offset += len(text_in) * 6 + 20
            text_in = str(player.current_bid)
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            x_offset += len(text_in) * 6 + 20
            text_in = 'Money left:'
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            x_offset += len(text_in) * 6 + 20
            text_in = str(player.money)
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            x_offset += len(text_in) * 6 + 20
            text_in = 'Time left:'
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            x_offset += len(text_in) * 6 + 20
            text_in = str(player.time)
            self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')
            y_offset += 45

        self.w.create_line(0, y_offset, 600, y_offset)
        x_offset = 10
        y_offset += 30
        # draself.w.head
        x_offset += 400
        text_in = 'Goal: ' + str(self.goal) + ' similar items'
        self.w.create_text((x_offset, y_offset), text=text_in, justify='left', anchor='nw')

        self.w.update()


    #TODO: COMMUNICATION WITH SERVER - MAIN SCRIPT IS HERE
    #TODO: DISPLAY WINNER OF THE GAME
    #Overloaded function:
    #for every given bid: id,bid,time_used (for every team)
    #if item is won: id,-1 (only once for the winner)
    #if game is won: id only for the winner
    def update(self, pid, bid=-2, time_used=0):
        if bid >=0:
            self.players[pid].update(bid,time_used)
            self.draw_scoreboard()
        elif bid==-1:
            for i in range(len(self.players)):
                if i == pid:
                    self.players[i].update(0,0,self.current_item)
                    self.last_winner = self.players[i].teamname
                    self.last_item = self.current_item
                    self.current_item = self.itemlist.pop(0)
                else:
                    self.players[i].update(0,0)

            self.draw_scoreboard()
        elif bid == -2:
            self.draw_scoreboard(pid)

if __name__ == "__main__":
    '''EXAMPLE'''
    #Visualizer is created with goal of 3, 2 players and an itemlist
    v = Visualizer(3,[('mark',120),('tom',150)],[3,4,3,3,2,1,2,0,3,4])


    v.update(0,10,15) #Player 0, Bid 10, Time used 15
    time.sleep(2)
    v.update(1,10,20) #Player 1, Bid 10, Time used 20
    time.sleep(2)
    v.update(0,-1) # Player 0 wins the item
    time.sleep(2)
    v.update(0,10,15)
    time.sleep(2)
    v.update(1,15,20)
    time.sleep(2)
    v.update(1,-1)
    time.sleep(2)
    v.update(0,10,15)
    time.sleep(2)
    v.update(1,10,20)
    time.sleep(2)
    v.update(0,-1)
    time.sleep(2)
    v.update(0,10,15)
    time.sleep(2)
    v.update(1,10,20)
    time.sleep(2)
    v.update(0,-1)
    v.update(0) #Player 0 wins the game
    v.w.mainloop()
