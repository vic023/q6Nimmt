import tkinter as tk
from tkinter import scrolledtext
import random # to generate random cards for testing
import socket
import threading
import json

from game_objs import *
from board import Board
from scoreboard import Scoreboard
from hand import Hand
from ops import OpsSelection
from discardpile import DiscardPile
from log import Log
from q6_constants import *

"""
client.py

Consolidates all the gui objects to form the in-game client and handles network
communication between server and player. Displays game state and transmits
appropriate player actions to the server (which keeps track of the entire game
state).

Board and hand are expected to have been initialized by the server before their
conception so they take the hand and rows as arguments.
"""

class GameViewClient:

    # TODO: make it so that gamestate is not required upon instantiation
    # seems incorrect to have it take in gamestate...
    def __init__(self, master, gamestate, conn):

        board, players, hand, pid = unpackGamestate(gamestate)

        self.master = master
        self.master.title('Q6Nimmt!')

        # connection to the server
        self.conn = conn

        # id of the player
        self.pid = pid

        # keep track of all player names in the order they're given
        self.pNames = [p.name for p in players]

        # board and scrollable scoreboard (currently janky display)
        self.topFrame = tk.Frame(self.master)
        self.boardFrame = tk.Frame(self.topFrame)
        self.board = Board(self.boardFrame, board)
        self.sbFrame = tk.Frame(self.topFrame)
        self.scoreboard = Scoreboard(self.sbFrame, players, self.pid)
        self.boardFrame.pack(side=tk.LEFT)
        self.sbFrame.pack(side=tk.LEFT)
        self.topFrame.pack(side=tk.TOP)

        self.discardFrame = tk.Frame(self.master)
        self.discardPile = DiscardPile(self.discardFrame)
        self.discardPile.pack(side=tk.TOP)
        self.discardFrame.pack(side=tk.TOP)

        # update ket button functions
        def chooseRow(row):
            data = {TARGET: row}
            self.conn.sendall(json.dumps(data).encode(FORMAT))
            self.board.disableKets()
        for r, ketButton in enumerate(self.board.ketButtons):
            ketButton.config(command=lambda sel_r=r:chooseRow(sel_r))
        self.board.disableKets()


        # hand, op selection, confirmation button
        self.midFrame = tk.Frame(self.master)
        self.hand = Hand(self.midFrame, hand)
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

        # receive game state via another thread
        self.recvThread = threading.Thread(target=self.recvGameState, args=())
        self.recvThread.daemon = True
        self.recvThread.start()

    """
    The function used to transmit the player's selected card to discard along with
    the quantum operation that the card will incur. Triggers when the "Confirm",
    button in the client is pressed.

    Sends the index of the card to be discarded from the player's hand, along
    with the selected quantum operation that the player selected to append to
    the wire of the quantum circuit.
    """
    def sendDiscard(self):
        data = {DISCARD:
                {DISCARD_IND: self.hand.discardInd.get(),
                 DISCARD_OP: self.ops.selectedOp.get()}}
        self.conn.sendall(json.dumps(data).encode(FORMAT))

    """
    Waits to receive data from server to update the board state.
    """
    def recvGameState(self):
        while True:

            if bool(self.conn):

                # game state updates (in JSON)
                message = json.loads(self.conn.recv(2048))

                # everyone has sent their discard, server should send the
                # last recorded discard (by index) of each player as a response
                # so that the client removes that selection from the display
                if TURN_START in message:
                    self.confirmButton.config(state="normal")

                elif TURN_IP in message:
                    self.confirmButton.config(state="disabled")
                    discardInd = message[TURN_IP]
                    self.hand.discardUpdate(discardInd)

                # prompt selection here for too low of a discard
                elif LOW_CARD in message:
                    self.board.enableKets()

                # the next turn, update the scoreboard
                elif TURN_END in message:
                    players = unpackPlayers(message[TURN_END][PLAYERS])

                    # disable mqops for player if they have run out
                    if players[self.pid].mqops == 0:
                        self.ops.disableMqops()
                        self.ops.selectedOp.set('')

                    # update scoreboard
                    self.scoreboard.updatePlayerInfo(players, self.pid)

                    # clear discards
                    self.discardPile.clearDiscards()

                elif DISCARDS in message:
                    # discards will be a list of cards in json form
                    # change them into card objects
                    discards = message[DISCARDS]
                    discards = [unpackCard(discard) for discard in discards]
                    self.discardPile.displayDiscards(discards, self.pNames)

                elif MQOP_PROMPT in message:
                    # message contains the source index
                    self.board.enableTargetKets(message[MQOP_PROMPT])

                # highlight the next discard to be processed within the queue
                elif HIGHLIGHT_NEXT in message:
                    self.discardPile.highlightNextDiscard()

                elif BOARD in message:
                    board = unpackBoard(message[BOARD])
                    self.board.updateBoard(board)

                elif LOG in message:
                    self.log.display(message[LOG])

                elif NEXT_ROUND in message:
                    gamestate = message[NEXT_ROUND]
                    board, players, hand, pid = unpackGamestate(gamestate)
                    if players[pid].mqops > 0:
                        self.ops.enableMqops()
                    self.pid = pid
                    self.board.updateBoard(board)
                    self.players.updatePlayerInfo(players, self.pid)
                    self.hand.displayNewHand(hand)
                    self.confirmButton.config(state="normal")


                elif PLAYERS in message:
                    self.scoreboard.updatePlayerInfo(unpackPlayers(message[PLAYERS]))

                elif GAME_OVER in message:
                    break


        self.destroy()


# test all the guis put together without network packets
def gameClientTest():
    root = tk.Tk()
    hand = randomHand(10)
    hand.sort()
    rows = randomRows()
    players = [randomPlayer() for _ in range(10)]
    gamestate = {BOARD: [row.jsonRepr() for row in rows],
                 PLAYERS: [player.__dict__ for player in players],
                 HAND: hand.jsonRepr(),
                 PID: 7}
    app =  GameViewClient(root, gamestate, None)
    root.mainloop()



if __name__ == '__main__':
    gameClientTest()

