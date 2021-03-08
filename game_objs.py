import random
import string
import time

from qiskit import *
from qiskit.quantum_info import Statevector
from qiskit.circuit.library.standard_gates import *

from q6_constants import *

"""
Contains the definitions of the data structures used to represent in-game
objects.
"""
class Card(object):

    """
    number  - affects order in which cards are placed
    score   - affects player score
    gate    - the gate that the card contains (stored as string, e.g. 'X', 'CX')
    onwerid - the player that placed the card
    """

    def __init__(self, number, score, op, ownerid=-1):
        self.number = number
        self.score = score
        self.op = op
        self.ownerid = ownerid

    def __gt__(self, o):
        return self.number > o.number

    def __lt__(self, o):
        return self.number < o.number

    def inHandRep(self):
        return f'{self.number}\n({abs(self.score)})'

    # for printing to console
    def __str__(self):
        return f'{self.number} ({abs(self.score)}) [{self.op}]'

    # representation on the board
    def boardRep(self):
        return f'{self.number}\n({abs(self.score)})\n[{self.op}]'

    def __repr__(self):
        return f'Number: {self.number}\nScore: {abs(self.score)}\nGate: {self.op}'

"""
Container for a group of cards (e.g. hand, row on board)
"""
class Pile(object):
    # one qubit per id to modify actual score, -1 for player hand
    def __init__(self, id=-1, qubit=0, list=[]):
        self.id = id
        self.qubit = qubit
        self.list = list

    def count(self):
        return len(self.list)

    def isEmpty(self):
        return bool(self.list)

    def addCard(self, card):
        self.list.append(card)

    # discards
    def discard(self, index):
        try:
            del self.list[index]
        except:
            pass

    def draw(self):
        try:
            return self.list.pop()
        except IndexError:
            return None

    # clear the row, and obtain measured qubit
    def replaceRow(self, result):
        self.list = []
        self.qubit = result

    # sum of score should be cards removed, only up to 5 are removed
    # while the last card always remains to form the new row
    def score(self):
        return sum([c.score for c in self.list])

    # cards sorted for convenient viewing in players' hands
    def sort(self):
        self.list.sort()

    # something wrong if this returns None
    def lastCard(self):
        return self.list[-1] if self.count() > 0 else None

    def printCards(self):
        print(', '.join([str(c) for c in self.list]))

    def __str__(self):
        return f'Pile #{self.id}, {self.count()} card(s), {self.score()} points'

    def __repr__(self):
        return f'Pile #{self.id}, {self.count()} card(s), {self.score()} points\n' + \
               ', '.join([str(c) for c in self.list]) + '\n'

    def jsonRepr(self):
        return dict(id=self.id, list=[c.__dict__ for c in self.list])



class Player(object):
    def __init__(self, id, name, score=STARTING_SCORE, mqops=STARTING_MQOPS):
        self.id = id
        self.name = name
        self.score = score
        self.mqops = mqops # resource for multi-qubit operations

"""
Tracks game state.
"""
class Game(object):

    """
    Player order determines player data order (e.g. hands, discards)
    """

    # players is assumed to be a simple list of player names
    def __init__(self, players):
        self.players = [Player(i, pn) for i, pn in enumerate(players)]

    # called at the start of a new round
    # makes a deck, deals cards, and makes the 4 rows from the remaining deck
    def newRound(self):
        self.sv = Statevector.from_label("0000")
        self.circuit = QuantumCircuit(4)
        self.cnot_id = 0
        self.hswap_id = 0
        self.turn = 0
        self.discards = [None for _ in range(len(self.players))]

        deck = self.makeDeck()
        self.hands = [None for p in range(len(self.players))]
        for p in range(len(self.players)):
            hand = []
            for _ in range(HANDSIZE):
                card = deck.draw()
                card.ownerid = p
                hand.append(card)
            self.hands[p] = Pile(list=hand)
            self.hands[p].sort()
            # reset mqops each round
            self.players[p].mqops = STARTING_MQOPS
        self.board = [Pile(i, list=[deck.draw(),]) for i in range(4)]

    # makes and shuffles a new deck of cards
    def makeDeck(self):
        cards = []
        for i in range(1, 105):
            if i == 55:
                score = 7
            elif i % 11 == 0:
                score = 5
            elif i % 10 == 0:
                score = 3
            elif i % 5 == 0:
                score = 2
            else:
                score = 1
            cards.append(Card(i, score, ''))
        random.shuffle(cards)
        return Pile(list=cards)

    # turns indices and gates into cards to be appended to rows by server
    def prepareDiscards(self):
        self.turn += 1
        discards = []
        for pid, (discardInd, op) in enumerate(self.discards):
            card = self.hands[pid].list[discardInd]
            if op == 'hSwap' or op == 'CNot':
                self.players[pid].mqops -= 1
            card.op = op
            discards.append(card)
            self.hands[pid].discard(discardInd)
        self.discards = discards
        self.discards.sort()

    # returns a list of filled rows by index [0,3]
    def maxedRows(self):
        return [i for i in range(len(self.board)) if self.board[i].count() >= 5]

    # append for multi-qubit operation, syncing the columns of the affected rows
    def appendMQOP(self, discard, controlRow, targetRow, targetRowOldLC):

        op = discard.op

        # Labelling
        #CX_T stands for CNot Target
        target_op = f'CX_T{self.cnot_id}' if op == 'CNot' else f'hSwap{self.hswap_id}'
        #CX_S stands for CNot Source
        discard.op = f'CX_S{self.cnot_id}' if op == 'CNot' else f'hSwap{self.hswap_id}'

        # LC = Last card, inherit only number of last card
        targetRowNewLC = Card(targetRowOldLC.number, 0, target_op, discard.ownerid)

        # append filler cards to the row with less cards
        fillerCard = Card(0, 0, '')
        numOfFiller = abs(self.board[controlRow].count() - self.board[targetRow].count())
        if self.board[controlRow].count() > self.board[targetRow].count():
            for _ in range(numOfFiller):
                self.board[targetRow].addCard(fillerCard)

        elif self.board[controlRow].count() < self.board[targetRow].count():
            for _ in range(numOfFiller):
                self.board[controlRow].addCard(fillerCard)

        # append source and target row of cards
        self.board[controlRow].addCard(discard)
        self.board[targetRow].addCard(targetRowNewLC)

        # apply operation on quantum circuit
        if op == 'CNot':
            self.circuit.cx(controlRow, targetRow)
            self.cnot_id += 1
        if op == 'hSwap':
            self.circuit.cx(controlRow, targetRow)
            self.circuit.csx(targetRow, controlRow)
            self.circuit.cx(controlRow, targetRow)
            self.hswap_id += 1

    def appendOP(self, discard, affectedRow):
        op = discard.op

        if op == 'H':
            self.circuit.h(affectedRow)
        elif op == 'Z':
            self.circuit.z(affectedRow)
        else:
            discard.op = ''

        self.board[affectedRow].addCard(discard)




    # return the index (relative to current board) to append the discard,
    # -1 if no suitable row exists (i.e. card too low)
    def tryDiscard(self, discard):
        lastCards = [row.lastCard() if bool(row.lastCard()) else -1 for row in self.board]
        dummyCard = Card(-1,0,'')
        candidate = max([card for card in lastCards if card < discard] + [dummyCard])
        if candidate == dummyCard:
            return -1
        else:
            return lastCards.index(candidate)


    # check whether terminating condition has been reached
    def gameHasEnded(self):
        return bool([p for p in self.players if p.score <= 0])

    # find the winner(s)
    def findWinner(self):
        winners = [self.players[0]]
        for p in self.players[1:]:
            if winners[0].score < p.score:
                winners = [p,]
            elif winners[0].score == p.score:
                winners.append(p)
        return [w.name for w in winners]

    # measure, calculate score from measurement, replace cards of row measured
    def measureRow(self, rowInd, ownerid):

        # time operations
        startTime = time.time()
        # apply queued list of operations
        self.sv = self.sv.evolve(self.circuit)
        print(f"Application of quantum operations finished in {time.time() - startTime} seconds.")
        # clear the queue of quantum operations
        self.circuit = QuantumCircuit(4)
        startTime = time.time()

        # measure the system
        result, self.sv = self.sv.measure([rowInd])
        print(f"Measurement finished in {time.time() - startTime} seconds.")
        self.calculateScore(rowInd, result, ownerid)
        self.board[rowInd].replaceRow(result)

        return float(result)


    # substract score based on measurement of qubit and the person who measured
    def calculateScore(self, rowInd, qbitMeas, ownerid):

        num_OtherPlayers = len(self.players) - 1

        # don't divide by zero
        num_OtherPlayers = num_OtherPlayers if num_OtherPlayers > 0 else 1

        # how the points rae split between the rest of the players
        dampeningFactor = 1.0 / num_OtherPlayers

        # measurement is numpy string, change it to float
        qbitMeas = float(qbitMeas)

        # penalize player for |0> measurement
        self.players[ownerid].score -= (1 - qbitMeas) * self.board[rowInd].score()

        # subtract from other players for |1> measurement, with penalty
        # divided by the number of other players
        for otherPlayer in self.players[:ownerid] + self.players[ownerid+1:]:
            otherPlayer.score -= qbitMeas * self.board[rowInd].score() * dampeningFactor


# helper functions that turn dictionaries into python game objects
def unpackCard(card):
    return Card(*tuple(card[key] for key in card.keys()))

def unpackPile(pile):
    p = tuple(pile[key] for key in pile.keys())
    plist = [unpackCard(c) for c in p[1]]
    return Pile(p[0], plist)

def unpackBoard(board):
    return [unpackPile(row) for row in board]

def unpackPlayers(players):
    return [Player(*tuple(p[key] for key in p.keys())) for p in players]

def unpackGamestate(gamestate):
    board = unpackBoard(gamestate[BOARD])
    players = unpackPlayers(gamestate[PLAYERS])
    hand = unpackPile(gamestate[HAND])
    pid = gamestate[PID]

    return board, players, hand, pid

def randomPlayerName():
    name = ''.join(random.choice(string.ascii_lowercase) for i in range(7))
    return name.capitalize()

def randomPlayer():
    if not hasattr(randomPlayer, "pid"):
        randomPlayer.pid = -1
    randomPlayer.pid += 1
    return Player(randomPlayer.pid, randomPlayerName(), random.randint(-10,66), random.randint(0,3))

def randomCard():
    gates = ['hSwap', 'CX', 'Z', 'H', '']
    return Card(random.randint(1,104), random.randint(-7, -1), random.choice(gates))

def randomRows():
    rows = []
    for i in range(4):
        row = []
        numofCards = random.randint(1,6)
        for c in range(numofCards):
            card = randomCard()
            row.append(card)
        rows.append(Pile(random.randint(0,104), list=row))
    return rows

def randomHand(numofCards = 6):
    return Pile(list=[randomCard() for _ in range(numofCards)])
