import tkinter as tk
from game_objs import *

import random # to generate random cards for testing
import threading
import time

class Board(tk.Frame):
    def __init__(self, master, rows):
        tk.Frame.__init__(self, master)
        self.rows = rows
        self.selectedRow = -1
        self.ketButtons = []
        self.generateKets()
        self.drawGrid()

    # to be called when board needs to be updated
    def updateBoard(self, rows):
        self.rows = rows
        self.drawGrid()

    def generateKets(self):
        def chooseRow(row):
            self.selectedRow = row

        for r in range(4):
            ketButton = tk.Button(self.master, height=5, text="|0>",
                                  command=lambda selected_row=r:chooseRow(selected_row))
            ketButton.grid(row=r, column=0)
            self.ketButtons.append(ketButton)


    def drawGrid(self):

        # command for buttons to select which row to take when forced to take a row
        # To be implemented as a send operation when network interface is implemented


        for r, row in enumerate(self.rows):
            for c in range(6):
                cardLabel = tk.Label(self.master, height=5, width=7, relief=tk.RAISED)
                # if there is a card, draw the card
                if c < row.count():
                    cardLabel.configure(text=row.list[c].boardRep(), relief=tk.SUNKEN)

                # 5th card yellow background
                if c == 4:
                    cardLabel.configure(bg="#CCCC77")

                # 6th card red background
                elif c == 5:
                    cardLabel.configure(bg="#CC7777")

                # other cards with grey background
                else:
                    cardLabel.configure(bg="#AAAAAA")

                cardLabel.grid(row=r, column=c+1)

    def enableKets(self):
        for ketButton, row in zip(self.ketButtons, self.rows):
            if row.id != -1:
                ketButton.config(state="normal")

    def enableTargetKets(self, rowInd):
        for ketButton, row in zip(self.ketButtons[:rowInd] + self.ketButtons[rowInd+1:],
                                  self.rows[:rowInd] + self.rows[rowInd+1:]):
            if row.id != -1:
                ketButton.config(state="normal")

    def disableKets(self):
        for ketButton in self.ketButtons:
            ketButton.config(state="disabled")



def BoardTest():
    root = tk.Tk()
    rows = randomRows()
    print('\n'.join([str(row) for row in rows]))
    app = Board(root, rows)

    def updateBoardTest():
        rows = randomRows()
        app.updateBoard(rows)
        print('\n'.join([str(row) for row in rows]))
        rows[0].printCards()

    def ketEnableTest():
        app.enableKets()

    def ketDisableTest():
        app.disableKets()
        root.after(5000, ketEnableTest)

    # root.after(5000, updateBoardTest)
    root.after(5000, ketDisableTest)
    root.mainloop()

def CNotExample():
    root = tk.Tk()
    rows = [Pile(0, [Card(20, -3, 'H'), Card(22, -3, 'Z'), Card(25, -3, 'H'), Card(29, -1, 'CX_S1')]),
            Pile(1, [Card(5, -2, ''), Card(0, 0, ''), Card(0, 0, ''), Card(5, 0, 'CX_T1')]),
            Pile(2, [Card(7, -2, ''),]),
            Pile(3, [Card(101, -1, 'H'),])]
    app = Board(root, rows)
    root.mainloop()

if __name__ == '__main__':
    # BoardTest()
    CNotExample()