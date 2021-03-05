import tkinter as tk
import threading
import string
import socket
import json
import time

from server import Server
from client import GameViewClient


from q6_constants import * # defined headers for q6nimmt network packets

class Lobby:
    def __init__(self, master, playerName, hosting, hostIP=''):

        self.master = master
        self.playerName = playerName

        # whether you are the room host or not
        self.hosting = hosting

        # default port to connect to
        self.port = 5600
        self.hostIP = hostIP

        # host's client will start a Server instance on a separate thread
        if self.hosting:
            self.server = Server()
            self.hostIP = self.server.ip
            server_thread = threading.Thread(target=self.server.lobby_wait, args=())
            server_thread.daemon = True
            server_thread.start()

        # Display Host's IP and Port
        self.top_frame = tk.Frame(self.master)
        self.ip_label = tk.Label(self.top_frame, text="Address: " + self.hostIP)
        self.ip_label.pack(side=tk.LEFT)
        self.port_label = tk.Label(self.top_frame, text="Port: " + str(self.port))
        self.port_label.pack(side=tk.LEFT)
        self.top_frame.pack(side=tk.TOP, pady=5)

        # Frame for scrollable list of players in lobby
        self.list_frame = tk.Frame(self.master)
        self.player_label = tk.Label(self.list_frame, text="Players")
        self.player_label.pack()
        self.scroll_bar = tk.Scrollbar(self.list_frame)
        self.scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
        self.players_display = tk.Text(self.list_frame, height=10, width=30)
        self.players_display.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.scroll_bar.config(command=self.players_display.yview)
        self.players_display.config(yscrollcommand=self.scroll_bar.set, background="#FEFEFE", highlightbackground="grey", state="disabled")
        self.list_frame.pack(side=tk.TOP, pady=5)

        # start and exit buttons
        self.bottom_frame = tk.Frame(self.master)
        self.btn_startGame = tk.Button(self.bottom_frame, text="Start Game", command=lambda : self.start_game(), state="disabled")
        self.btn_startGame.pack(side=tk.LEFT)
        self.btn_stopServer = tk.Button(self.bottom_frame, text="Exit", command=lambda : self.close_windows())
        self.btn_stopServer.pack(side=tk.LEFT)
        self.bottom_frame.pack(side=tk.BOTTOM, pady=5)

        if self.hosting:
            self.btn_startGame.config(state="normal")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.hostIP, self.port))
        waitThread = threading.Thread(target=self.waiting, args=())
        waitThread.daemon = True
        waitThread.start()

    def waiting(self):
        while True:
            try:
                message = json.loads(self.socket.recv(2048).decode(FORMAT))
                if NAME_REQ in message:
                    self.socket.send(json.dumps(self.playerName).encode(FORMAT))
                if DC in message:
                    self.player_label.config(text="Disconnected from host. Exiting in 5 seconds.")
                    time.sleep(5)
                    break

                # gamestarted, receive said gamestate within packet
                if NEXT_ROUND in message:
                    gamestate = message[NEXT_ROUND]
                    self.newWindow = tk.Toplevel(self.master)
                    self.app = GameViewClient(self.newWindow, gamestate,
                                              self.socket)
                    self.newWindow.grab_set()
                    break

                # update player list while in lobby
                if LOBBY_UPDATE in message:
                    self.update_player_list(message[LOBBY_UPDATE])
            except OSError:
                break

    # only host can start game
    def start_game(self):
        self.socket.send(json.dumps(START).encode(FORMAT))

    def close_windows(self):
        try:
            self.socket.send(json.dumps(DC).encode(FORMAT))
        except:
            pass
        self.socket.close()
        self.master.grab_release()
        self.master.destroy()


    def update_player_list(self, players):
        self.players_display.config(state=tk.NORMAL)
        self.players_display.delete('1.0', tk.END)

        for p in players:
            self.players_display.insert(tk.END, p + '\n')

        self.players_display.config(state=tk.DISABLED)