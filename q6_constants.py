FORMAT = "utf-8"
NAME_REQ = "NAME_REQ"
START = "START"
LOBBY_UPDATE = "LOBBY_UPDATE"
GAME_STATE = "GAME_STATE"
DC = "DISCONNECT"
READY = "READY"

# game state keys in game state data packet
BOARD = "BOARD"
PLAYERS = "PLAYERS"
HAND = "HAND" # only player's hand
PID = "PID"
LOG = "LOG"
TURN_START = "TURN_START" # waiting on everyone's discard
TURN_IP = "TURN_IP" # currently processing discards
TURN_END = "TURN_END" # all discards processed, turn has ended
LOW_CARD = "LOW_CARD" # card too low, prompt player to select row
TARGET = "TARGET" # selected row for either illegal discard or MQOP
NEXT_ROUND = "NEXT_ROUND" #reached the next round
UPDATE = "UPDATE"
DISCARD = "DISCARD" # player's discard
DISCARDS = "DISCARDS" # every players discard
DISCARD_IND = "DISCARD_IND" # index of the discarded card (wrt to player's hand)
HIGHLIGHT_NEXT = "HIGHLIGHT_NEXT" # highlight the next discard to be processed
DISCARD_OP = "DISCARD_OP" # the quantum operation that the player has selected
MQOP_PROMPT = "MQOP_PROMPT" # prompt player to select target qubit for multi-qubit operation
GAME_OVER = "GAME_OVER" # returns clients back to lobby

# game parameters
HANDSIZE = 10
SHOTS = 10
STARTING_SCORE = 30
MAX_QUBITS = 20 # 29 too high...
STARTING_MQOPS = 1 # number of multi-qubit operations each player can make
