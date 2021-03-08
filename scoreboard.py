from game_objs import Player, randomPlayer
import tkinter as tk
"""
Displays player information.
"""
class Scoreboard(tk.Frame):
    def __init__(self, master, players, pid):
        tk.Frame.__init__(self, master)

        #later: find a way to get rid of canvas whitespace without hardcoding width
        self.canvas = tk.Canvas(self, bd=0, height=350, width=90)
        self.scoreboard = tk.Frame(self.canvas)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(fill='both', expand=True, side=tk.LEFT)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.canvas.create_window(0, 0, window=self.scoreboard, anchor='nw', tags='self.scoreboard')
        self.scoreboard.bind("<Configure>", self.onConfigure)
        # self.canvas.bind_all("<MouseWheel>", self.on_vertical)
        self.playerInfos = []
        self.updatePlayerInfo(players, pid)
        self.grid(row=0, column=0, sticky='N')


    # updates name, score, and mqops of each player
    def updatePlayerInfo(self, players, pid):

        for p in self.playerInfos:
            p.destroy()

        self.playerInfos = []

        for i, p in enumerate(players):
            ptext = "\n".join([p.name, "Score: " + str(p.score), "Mqops: " + str(p.mqops)])
            playerInfo = tk.Label(self.scoreboard, width=10, text=ptext, relief=tk.RIDGE, justify=tk.LEFT)

            if i == pid:
                playerInfo.config(bg='#CCCCFF')
            else:
                playerInfo.config(bg='#CCCCCC')

            self.playerInfos.append(playerInfo)

        # find the player and set them as the first
        for id, pInfo in enumerate(self.playerInfos):
            if id == pid:
                toFront = pInfo
                break
        self.playerInfos.remove(toFront)
        self.playerInfos.insert(0, toFront)

        for i, playerInfo in enumerate(self.playerInfos):
            playerInfo.grid(row=i, column=0)

    def onConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_vertical(self, event):
        self.canvas.yview_scroll(-1* event.delta, "units")



def main():
    root = tk.Tk()

    players = [randomPlayer() for _ in range(10)]
    app = Scoreboard(root, players, 7)
    print('\n'.join([str(player.__dict__) for player in players]))
    def newScoreboard():
        players[7].mqops = 1337
        app.updatePlayerInfo(players, 7)
        print('\n'.join([str(player.__dict__) for player in players]))
    root.after(5000, newScoreboard)
    root.mainloop()

if __name__ == '__main__':
    main()
