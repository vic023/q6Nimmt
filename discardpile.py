import tkinter as tk
import random
import time
from game_objs import *

# allows players to view the discards when everyone has discarded
class DiscardPile(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.currDiscardInd = 0
        self.playerLabels = []
        self.discardLabels = []
        for col in range(10):
            playerLabel = tk.Label(self)
            playerLabel.grid(row=0, column=col)
            self.playerLabels.append(playerLabel)
            discardLabel = tk.Label(self, height=4, width=7, relief=tk.GROOVE)
            discardLabel.grid(row=1, column=col)
            self.discardLabels.append(discardLabel)


    def displayDiscards(self, discards, pNames):
        for col, card in enumerate(discards):
            self.playerLabels[col].config(text=pNames[card.ownerid])
            self.discardLabels[col].config(text=card.boardRep())

    def highlightNextDiscard(self):
        for discardLabel in self.discardLabels:
            discardLabel.config(bg="#FFFFFF")

        self.discardLabels[self.currDiscardInd].config(bg="#77FF77")
        self.currDiscardInd += 1


    def clearDiscards(self):
        for col in range(10):
            self.playerLabels[col].config(text='')
            self.discardLabels[col].config(bg="#FFFFFF", text='')
        self.currDiscardInd = 0

def discardpileTest():

    discards = [randomCard() for i in range(5)]
    for index, card in enumerate(discards):
        card.ownerid = index
    players = [randomPlayerName() for _ in range(5)]

    root = tk.Tk()

    app = DiscardPile(root)
    app.pack()

    highlightcount = 0

    def testDisplay():
        app.displayDiscards(discards, players)
        root.after(3000, testSort)


    def testSort():
        discards.sort()
        app.displayDiscards(discards, players)
        root.after(5000, testHighlight)

    def testHighlight():
        nonlocal highlightcount
        if highlightcount < 5:
            app.highlightNextDiscard()
            highlightcount += 1
            root.after(3000, testHighlight)
        else:
            root.after(5000, testClear)

    def testClear():
        app.clearDiscards()

    root.after(5000, testDisplay)

    root.mainloop()

if __name__ == '__main__':
    discardpileTest()
