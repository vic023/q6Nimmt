from game_objs import *
import tkinter as tk
import threading
import time

class Hand(tk.Frame):

    def __init__(self, master, hand):
        tk.Frame.__init__(self, master)
        self.master = master
        self.discardInd = tk.IntVar()
        self.handFont = ("Helvetica", "16")
        self.cardButtons = []
        self.displayNewHand(hand)

    def displayNewHand(self, hand):
        # dummy command for testing purposes, shows selection index
        # def showChoice():
        #     print(self.discardInd.get())

        for c in self.cardButtons:
            c.destroy()

        self.cardButtons = []

        for ind, card in enumerate(hand.list):
            cardButton =tk.Radiobutton(self, text=card.inHandRep(), indicatoron=0,
                           # command=showChoice,
                           font=self.handFont, height=3, width=4,
                           variable=self.discardInd, value=ind)
            cardButton.pack(side=tk.LEFT)
            self.cardButtons.append(cardButton)

    # update on client side what card has been discarded, and update the indices
    # of the following cards
    def discardUpdate(self, ind):

        self.cardButtons[ind].destroy()
        del self.cardButtons[ind]
        for i, c in enumerate(self.cardButtons):
            c.config(value=i)
        # select the first card by default, do nothing otherwise
        try:
            self.cardButtons[0].select()
        except:
            pass




def main():
    root = tk.Tk()
    hand = randomHand(10)
    app = Hand(root, hand)
    app.pack()
    print(hand)
    def discardTest():
        app.discardUpdate(1)
    root.after(5000, discardTest)
    def newHandTest():
        hand = randomHand(10)
        app.displayNewHand(hand)
    root.mainloop()

if __name__ == '__main__':
    main()

