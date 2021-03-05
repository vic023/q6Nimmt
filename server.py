import socket
import time # for sleep
import threading
import json
import sys

from game_objs import *
from q6_constants import *# defined headers for q6nimmt network packets

from qiskit import *
from qiskit.circuit.library.standard_gates import *



"""
Handles game state and communicating that game state to all connected players
who joined the game instance. Only server host should have one instance of this
process running. Thus server must have qiskit as prerequisite.
"""
class Server:
    def __init__(self):

        self.ip = '127.0.0.1' # figure out how to host on given domain
        self.port = 5600

        self.game = None
        self.gameEnded = False

        self.gameThread = None

        # the socket to listen to for new connections
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))

        self.lock = threading.Lock()


        # player index should match connection index, host should be index 0
        self.playerNames = []
        self.conns = []

        # hold client response to server prompts (LOW_CARD, mqop)
        self.response = None


    # main thread: waiting for people to show up and connect
    def lobby_wait(self):
        self.socket.listen()
        while not bool(self.game):
            try:
                if len(self.playerNames) < 10 and not bool(self.game):
                    conn, addr = self.socket.accept()
                    conn.sendall(json.dumps(NAME_REQ).encode(FORMAT))
                    name = json.loads(conn.recv(1024))
                    self.playerNames.append(name)
                    self.conns.append(conn)
                    print(f'{name} has joined!')
                    self.lobby_update() # update current lobby for everyone
                    thread = threading.Thread(target=self.connHandle, args=(conn,addr))
                    thread.start()
            except:
                print("Not exiting cleanly.")
                break
        print("Game has started.")

    def broadcast(self, data):
        for conn in self.conns:
            conn.sendall(data.encode(FORMAT))

    def lobby_update(self):
        self.broadcast(json.dumps({LOBBY_UPDATE: self.playerNames}))

    # broadcasts any game state updates to all players
    def log_update(self, info):
        self.broadcast(json.dumps({LOG: info}))

    # broadcasts the discards for the turn
    def broadcastDiscards(self):
        data = {DISCARDS: [c.__dict__ for c in self.game.discards]}
        self.broadcast(json.dumps(data))

    # broadcasts board updates
    def board_update(self):
        data = {BOARD: [row.jsonRepr() for row in self.game.board]}
        self.broadcast(json.dumps(data))

    # starts new round and broadcast updated game state to all players
    def startNewRound(self):
        self.game.newRound()
        data = {NEXT_ROUND:
                    {BOARD: [row.jsonRepr() for row in self.game.board],
                     PLAYERS: [player.__dict__ for player in self.game.players],
                     HAND: None,
                     PID: -1}}

        for pid, conn in enumerate(self.conns):
            data[NEXT_ROUND][HAND] = self.game.hands[pid].jsonRepr()
            data[NEXT_ROUND][PID] = pid
            conn.sendall(json.dumps(data).encode(FORMAT))

    def connHandle(self, conn, addr):

        while True:

            pid = self.conns.index(conn)

            try:
                message = json.loads(conn.recv(1024))
                ################## LOBBY LOGIC #######################
                # only host is able to start game, if the game hasnt already started
                if START in message and pid == 0 and not bool(self.game)  and not bool(self.gameThread):
                    self.lock.acquire()
                    self.game = Game(self.playerNames)

                    self.startNewRound()

                    # start another thread that handles game logic
                    self.gameThread = threading.Thread(target = self.playGame, args=())
                    self.gameThread.start()
                    self.lock.release()


                elif DC in message:
                    # if host disconnects, disconnect everyone
                    if self.conns.index(conn) == 0:
                        for c in self.conns[1:]:
                            c.sendall(json.dumps(DC).encode(FORMAT))
                            c.close()
                        self.socket.close()
                    else:
                        self.lock.acquire()
                        print(f"{self.playerNames[self.conns.index(conn)]} has disconnected.")
                        del self.playerNames[self.conns.index(conn)]
                        del self.conns[self.conns.index(conn)]
                        self.lock.release()
                        self.lobby_update()
                ########################################################

                ################## GAME LOGIC ######################
                # connection thread only handles receiving discards
                if DISCARD in message:
                    message = message[DISCARD]
                    self.lock.acquire()
                    self.game.discards[pid] = (message[DISCARD_IND], message[DISCARD_OP])
                    self.lock.release()

                # Target ket selection for low card or mqop
                elif TARGET in message:
                    self.lock.acquire()
                    self.response = message[TARGET]
                    self.lock.release()


                ###################################################
            except OSError:
                print("Game created.")
            except:
                print("An unexpected error ocurred.")
                break

    # server game logic here...
    # 2 major parts, game state and circuit
    def playGame(self):
        round = 0
        simulator = Aer.get_backend('qasm_simulator')
        while not self.gameEnded:

            # initialize new circuit
            circuit = QuantumCircuit(MAX_QUBITS)


            # round 0 already initializes the board...
            if round != 0:
                self.lock.acquire()
                self.startNewRound()
                self.lock.release()

            # round start
            for turn in range(HANDSIZE):

                # qubit limit reached, end the round
                if self.game.rowsRemaining() == 0:
                    break

                # prompt people to discard a card
                self.log_update("Select a card to discard.")
                time.sleep(2)
                self.broadcast(json.dumps(TURN_START))

                # wait for discards, yield to other threads
                while None in self.game.discards:
                    time.sleep(0)

                self.lock.acquire()

                for pid, (discardInd, _) in enumerate(self.game.discards):
                    # send response of last recorded index
                    self.conns[pid].sendall(json.dumps({TURN_IP: discardInd}).encode(FORMAT))

                # transform discard information to card objects, remove the card from respective hands
                self.game.prepareDiscards()

                time.sleep(3)

                # broadcast list of discards to display to everyone
                self.broadcastDiscards()
                time.sleep(3)

                # process discards
                for discard in self.game.discards:

                    if self.game.rowsRemaining() == 0:
                        break

                    self.broadcast(json.dumps(HIGHLIGHT_NEXT))
                    time.sleep(3)

                    # remove multi-qubit operation if there is only one row left
                    if self.game.rowsRemaining() < 2 and discard.op in ['CNot', 'hSwap']:
                        discard.op = ''
                        self.log_update("Only one row left, the multi-qubit operation shall be ignored.")
                        time.sleep(3)

                    # try to append the card to the row
                    append_rowInd = self.game.tryDiscard(discard)

                    # discard too low, prompt selection of row
                    if append_rowInd == -1:

                        # remove the operation
                        discard.op = ''

                        # notify everyone a selection must be made by the player
                        # who discarded the card
                        self.log_update(f"{self.playerNames[discard.ownerid]}'s discard is too low. {self.playerNames[discard.ownerid]} please select a row to take.")

                        time.sleep(3)

                        # enable row selection for the player
                        self.conns[discard.ownerid].sendall(json.dumps(LOW_CARD).encode(FORMAT))

                        # receive selected row
                        self.lock.release()
                        while not bool(self.response):
                            time.sleep(0)
                        self.lock.acquire()

                        selection = self.response
                        self.response = None
                        self.log_update(f"{self.playerNames[discard.ownerid]} has taken the {self.ind_to_pos(selection)} row.")
                        self.game.board[selection].addCard(discard)

                        # add to the list of piles that the player has taken
                        takenPile = self.game.replaceRows([selection,])

                        time.sleep(3)

                        # broadcast updated board state
                        self.board_update()
                        time.sleep(5)
                        continue

                    # card is multi-qubit operation
                    if discard.op in ['CNot', 'hSwap']:
                        # prompt player for target selection
                        self.log_update(f"{self.playerNames[discard.ownerid]} has chosen to apply {discard.op}." +
                                        f" {self.playerNames[discard.ownerid]}, please select a target row with" +
                                        f" {self.ind_to_pos(append_rowInd)} row as the source.")
                        time.sleep(3)
                        self.conns[discard.ownerid].sendall(json.dumps({MQOP_PROMPT: append_rowInd}).encode(FORMAT))

                        self.lock.release()
                        while not bool(self.response):
                            time.sleep(0)
                        self.lock.acquire()

                        targetInd = self.response
                        self.response = None

                        # broadcast target selection
                        self.log_update(f"The target is the {self.ind_to_pos(targetInd)} row.")

                        # apply operation to circuit
                        if discard.op == 'CX':
                            circuit.cx(self.game.board[append_rowInd].id, self.game.board[targetInd].id)

                        if discard.op == 'hSwap':
                            circuit.cx(self.game.board[append_rowInd].id, self.game.board[targetInd].id)
                            circuit.csx(self.game.board[targetInd].id, self.game.board[append_rowInd].id)
                            circuit.cx(self.game.board[append_rowInd].id, self.game.board[targetInd].id)

                        # fill out both rows to sync columns together
                        self.game.appendMQOP(discard, append_rowInd, targetInd)

                    # card is single qubit operation
                    else:
                        if discard.op == 'H':
                            circuit.h(self.game.board[append_rowInd].id)

                        elif discard.op == 'Z':
                            circuit.z(self.game.board[append_rowInd].id)

                        # discard.op == '(none)'
                        else:
                            discard.op = ''

                        self.game.board[append_rowInd].addCard(discard)

                    # broadcast new board status
                    time.sleep(3)
                    self.board_update()
                    time.sleep(3)

                    # after appending operations to circuit make
                    # row replacements if there are any to make
                    maxedrow_inds = self.game.maxedRows()
                    takenPiles = self.game.replaceRows(maxedrow_inds)
                    pid = discard.ownerid

                    # broadcast row replacements in log
                    if bool(takenPiles):
                        self.log_update(f"{self.playerNames[pid]} has taking the" +
                                " following rows with the following scores" +
                                f"{[(self.ind_to_pos(row_ind), qubitId, score) for row_ind, qubitId, score in takenPiles]}")
                        time.sleep(3)
                        self.board_update()
                        time.sleep(5)

                # end of processing discards
                self.game.discards = [None for _ in range(len(self.game.players))]

                # all discards processed, round continues...
                self.broadcast(json.dumps({TURN_END: {PLAYERS: [p.__dict__ for p in self.game.players]}}))
                time.sleep(3)

                self.lock.release()


            # calculate score here given qubit count results
            self.lock.acquire()
            circuit.measure_all()
            job = execute(circuit, simulator, shots=10)
            results = job.result()
            counts = results.get_counts()

            previousScores = [p.score for p in self.game.players]

            # deduct points accordingly
            processed_counts = self.processCounts(counts)
            self.game.calculateScore(processed_counts)

            # print each player's score differential to log
            currScores = [p.score for p in self.game.players]
            scoreDiffs = [currScore - previousScore for currScore, previousScore in zip(currScores, previousScores)]

            for p, scoreDiff in zip(self.playerNames, scoreDiffs):
                self.log_update(f"{p}: {scoreDiff}")
                time.sleep(3)

            # update everyone's scoreboard
            self.broadcast(json.dumps({PLAYERS: [p.__dict__ for p in self.game.players]}))
            time.sleep(5)

            self.gameEnded = self.game.gameHasEnded()
            round += 1
            self.lock.release()

        # game ended, announce winner(s)
        winners = self.game.findWinner()
        self.game.log_update(f"{winners} has won the game!!!")
        time.sleep(3)
        self.game.log_update("Returning to lobby in 60 seconds.")

        time.sleep(60)
        self.broadcast(GAME_OVER)

    # process counts given by the circuit constructed during the round
    # returns the number of times each qubit has measured |1> out of the number of shots taken
    def processCounts(self, counts):
        processed_counts = [0 for _ in range(self.game.nextQubitId)]
        for res in counts.keys():
            # indices are reversed
            for ind, qbit in enumerate(res[::-1]):
                if qbit == '1':
                    processed_counts[ind] += counts[res]
        return [pc/SHOTS for pc in processed_counts]

    def ind_to_pos(self, index):
        return ["1st", "2nd", "3rd", "4th"][index]






"""
Server blueprint

There should be {id: connection for enumerate(connection)}

#################
Lobby logic - waiting():
while True:
    receive msg
    if msg == start:
        newGame()

        break
    # message is a new connection
    else:
        add the new player to the list
        update everyone's lobby ui with a broadcast



Game Thread logic:

Game start - playGame()
    while not anyone's score <= 0:
        game.initializeRound()
        broadcast public info, send hands privately
        while cards still in hand (i.e. turn <= 10, if starting from 1):
            listen for everyone's discard (discards are ordered by player id)
            sort the discards
            broadcast queue (discards labelled with respective player's names)
            for discard in discards:
                if min(current rows) > discard:
                    prompt discard owner to select a row, listen
                    sum the row, record qubit id, append to player's qubit held
                    replace selected row with discard (possibly replace with an X-gate to the new qubit)
                    send queue & board update to all players
                    wait(3)
                    continue
                append to max(rows < card), said row is source
                if discard is multi-qubit operation ('CX', 'rtSwap'):
                    prompt discard owner to select row for target, listen
                    if target < source:
                        append filler cards to target, last filler card inherits previous non-filler card value
                    elif target > source:
                        append filler cards to source, last card is still the normal discard
                    apply mqop to source & target on circuit
                else:
                    apply op to qubit on circuit
                broadcast board update
                wait(2)
                maxedrows [row if len(row) == 6 for row in rows]
                for maxedrow in maxedrows:
                    sum the row, record qubit id, append to player's qubit held
                    allocate id for new qubit
                    replace with new row on board (so remember each old row's index on board)
                    append new row with card with gate removed
                    broadcast board update
                    wait(2)
                # end of discards loop
            cards in hand -= 1
            # end of round (end of cards are in hand loop)
        10 shots, tabulate scores, broadcast calculations
        wait(2)
    # end of game
    broadcast winner (i.e. max(find player(s) with max score))
"""


