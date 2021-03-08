import tkinter as tk
import random # for shuffling players
import threading

from game_objs import *
from board import Board
from scoreboard import Scoreboard
from hand import Hand
from ops import OpsSelection
from discardpile import DiscardPile
from log import Log
from q6_constants import *

"""
game_sim.py

An offline simulation of the game where all the players are controlled
iteratively by one person. Thus, the control flow of the game is also
implemented here as well.
"""
class GameSim:


    def __init__(self, master, players):

        self.game = Game(players)
        self.game.newRound()

        self.master = master
        self.master.title('Q6Nimmt!')

        # id of the player
        self.current_pid = 0
        self.targetRow = None

        # keep track of all player names in the order they're given
        self.pNames = players
        self.numofPlayers = len(self.pNames)

        # board and scrollable scoreboard
        self.topFrame = tk.Frame(self.master)
        self.boardFrame = tk.Frame(self.topFrame)
        self.board = Board(self.boardFrame, self.game.board)
        self.sbFrame = tk.Frame(self.topFrame)
        self.scoreboard = Scoreboard(self.sbFrame, self.game.players, self.current_pid)
        self.boardFrame.pack(side=tk.LEFT)
        self.sbFrame.pack(side=tk.LEFT)
        self.topFrame.pack(side=tk.TOP)

        self.discardFrame = tk.Frame(self.master)
        self.discardPile = DiscardPile(self.discardFrame)
        self.discardPile.pack(side=tk.TOP)
        self.discardFrame.pack(side=tk.TOP)

        # update ket button functions
        def chooseRow(row):
            self.targetRow = row
            self.board.disableKets()
        for r, ketButton in enumerate(self.board.ketButtons):
            ketButton.config(command=lambda sel_r=r:chooseRow(sel_r))
        self.board.disableKets()


        # hand, op selection, confirmation button
        self.midFrame = tk.Frame(self.master)
        self.hand = Hand(self.midFrame, self.game.hands[self.current_pid])
        self.opsFrame = tk.Frame(self.midFrame)
        self.ops =  OpsSelection(self.midFrame)
        self.confirmButton = tk.Button(self.midFrame, text="Confirm", command=lambda: self.sendDiscard())
        self.hand.pack(side=tk.LEFT)
        self.ops.pack(side=tk.LEFT)
        self.confirmButton.pack(side=tk.LEFT)
        self.midFrame.pack(side=tk.TOP)

        # game log
        self.logFrame = tk.Frame(self.master, relief=tk.RIDGE, bd=3)
        self.log = Log(self.logFrame)
        self.log.pack()
        self.logFrame.pack(side=tk.TOP)

        self.gameThread = threading.Thread(target=self.commenceGame, args=())
        self.gameThread.daemon = True
        self.gameThread.start()


    """
    The function used to transmit the player's selected card to discard along with
    the quantum operation that the card will incur. Triggers when the "Confirm",
    button in the client is pressed.

    Sends the index of the card to be discarded from the player's hand, along
    with the selected quantum operation that the player selected to append to
    the wire of the quantum circuit.

    Goes to the next player if one exists, otherwise the turn starts and the
    views displayed is based on the order of the sorted discards.
    """
    def sendDiscard(self):

        self.game.discards[self.current_pid] = (self.hand.discardInd.get(), self.ops.selectedOp.get())
        self.log.display(f"{self.pNames[self.current_pid]} has chosen a card to discard!")

        # go to next player, update view to that players POV
        if self.current_pid < self.numofPlayers - 1:
            self.current_pid += 1
            self.loadPlayer()


    """
    Load the current player's view (determined by self.current_pid)
    """
    def loadPlayer(self):
        pid = self.current_pid
        # three things need update, scoreboard, opselection, hand
        if self.game.players[pid].mqops > 0:
            self.ops.enableMqops()
        else:
            self.ops.disableMqops()
        self.scoreboard.updatePlayerInfo(self.game.players, pid)
        self.hand.displayNewHand(self.game.hands[pid])
        self.confirmButton.config(state="normal")

    """
    Starts the process of appending discards, changing the view to the player
    whose discard is being appended.

    Will prompt the player if a target row needs to be selected.
    """
    def commenceGame(self):
        while True:

            while None in self.game.discards:
                time.sleep(0)

            self.game.prepareDiscards()
            self.discardPile.displayDiscards(self.game.discards, self.pNames)
            for discard in self.game.discards:

                self.current_pid = discard.ownerid
                current_player = self.pNames[self.current_pid]
                self.loadPlayer()
                time.sleep(2)
                self.discardPile.highlightNextDiscard()
                time.sleep(2)

                appendInd = self.game.tryDiscard(discard)

                # card too low
                if appendInd == -1:
                    self.log.display(f"{current_player} has discarded a card too "+
                                    "low, so the quantum operation will be " +
                                    "ignored! Any mqop used is considered spent! " +
                                    f"{current_player}, please select a row to " +
                                    "take and its qubit will be measured.")

                    # wait for player's selection
                    tgt_prompt_thread = threading.Thread(target=self.recvTgt, args=())
                    tgt_prompt_thread.start()
                    self.board.enableKets()
                    tgt_prompt_thread.join()
                    targetInd = self.targetRow
                    self.targetRow = None

                    self.log.display(f"{current_player} has taken the {ind_to_pos(targetInd)} row.")
                    result = self.game.measureRow(targetInd, discard.ownerid)
                    time.sleep(2)

                    self.broadcastMeasRes(result, discard.ownerid)
                    time.sleep(2)
                    discard.op = ''
                    self.game.appendOP(discard, targetInd)

                else:
                    maxed_rows = self.game.maxedRows()

                    # card is multi-qubit operation
                    if discard.op in ['CNot', 'hSwap']:
                        # prompt player for target selection
                        self.log.display(f"{current_player} has chosen to apply {discard.op}. " +
                                        f"{current_player}, please select a target row with " +
                                        f"{ind_to_pos(appendInd)} row as the control/1st row of 2 rows.")

                        # wait for player's selection
                        tgt_prompt_thread = threading.Thread(target=self.recvTgt, args=())
                        tgt_prompt_thread.start()
                        self.board.enableTargetKets(appendInd)
                        tgt_prompt_thread.join()
                        targetInd = self.targetRow
                        self.targetRow = None

                        # broadcast target selection
                        self.log.display(f"The target shall be the {ind_to_pos(targetInd)} row.")

                        targetRowLC = self.game.board[targetInd].lastCard()

                        # if either one of the rows has 5 cards, force a measurement
                        # on BOTH rows
                        if targetInd in maxed_rows or appendInd in maxed_rows:
                            self.log.display("One of the rows is maxed out on cards! "
                                + "Both rows shall be replaced and their respective qubits measured.")
                            for row_ind in [appendInd, targetInd]:
                                self.log.display(f"{current_player} has taken the {ind_to_pos(row_ind)} row.")
                                result = self.game.measureRow(row_ind, discard.ownerid)
                                time.sleep(2)
                                self.broadcastMeasRes(result, discard.ownerid)
                                time.sleep(2)
                                self.loadPlayer()
                                time.sleep(2)

                        # fill out both rows to sync columns together
                        self.game.appendMQOP(discard, appendInd, targetInd, targetRowLC)

                    else:
                        if appendInd in maxed_rows:
                            self.log.display(f"The row {ind_to_pos(appendInd)} is maxed out on cards! "
                                + f"It shall be taken by {current_player} and its qubit measured!")
                            result = self.game.measureRow(appendInd, discard.ownerid)
                            time.sleep(2)
                            self.broadcastMeasRes(result, discard.ownerid)
                            time.sleep(2)
                            self.loadPlayer()
                            time.sleep(2)
                        self.game.appendOP(discard, appendInd)

                self.board.updateBoard(self.game.board)
                time.sleep(2)

            # progress to next turn if one exists
            self.endTurn()

    """
    Print a message telling the result of the measurement and who measured to
    the game log.
    """
    def broadcastMeasRes(self, result, discardOwner):
        if result:
            self.log.display(f"The qubit measured |1>! Points will be deducted from everyone else!")
        else:
            self.log.display(f"The qubit measured |0>! Points will be deducted from {self.pNames[discardOwner]}!")


    """
    Handles whether the last turn of the round has ocurred, and whether the
    round was the last one. The round ends when all cards have been discarded.
    When one player has reached 0 or less points, the round is considered to be
    the last, and is played through until the all cards are discarded.
    """
    def endTurn(self):
        # round has not ended, continue
        if self.game.turn < HANDSIZE:
            self.current_pid = 0
            self.discardPile.clearDiscards()
            self.game.discards = [None for _ in range(len(self.game.players))]
            self.loadPlayer()

        # round ended, check to see if there's a winner
        else:
            if self.game.gameHasEnded():
                winners = self.game.findWinner()
                self.broadcastWinners(winners)
                self.log.display("Game is now over, feel free to exit the simulation.")
                while True:
                    time.sleep(0)
            else:
                self.game.newRound()
                self.current_pid = 0
                self.discardPile.clearDiscards()
                self.board.updateBoard(self.game.board)
                self.loadPlayer()

    """
    Waits to receive target selection from the current player.
    """
    def recvTgt(self):
        self.targetRow = None
        while self.targetRow is None:
            time.sleep(0)

    def broadcastWinners(self, winners):
        if len(winners) == 1:
            self.log.display(f"{winners[0]} is the winner!")
        else:
            self.log.display(f"{winners} are the winners!")

def ind_to_pos(index):
    return ["1st", "2nd", "3rd", "4th"][index]


# test all the guis put together without network packets
def gameSimTest(numofPlayers=3):
    root = tk.Tk()
    players = ['Alice', 'Bob', 'Q.A.O.A.', 'Shor', 'Bernstein', 'Vazirani', 'Deutsch', 'Jozsa']
    random.shuffle(players)
    players = players[:numofPlayers]
    app =  GameSim(root, players)
    root.mainloop()



if __name__ == '__main__':
    gameSimTest()
