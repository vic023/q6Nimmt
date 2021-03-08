import socket
import threading
import tkinter as tk
from time import sleep

# game objects (all game logic implemented server side)
# from card import Card
# from pile import Pile
# from player import Player
# from qiskit import *
# from qiskit.circuit.library.standard_gates import *

# client window
from lobby import Lobby

# main menu
class Q6nimmt:
    def __init__(self, master):

        self.master = master
        self.master.title('Q6Nimmt!')

        # top text
        self.top_frame = tk.Frame(self.master)
        self.top_txt = tk.Label(self.top_frame, text="Main Menu") # serves to notify user
        self.top_txt.pack(side=tk.LEFT)
        self.top_frame.pack(side=tk.TOP, pady=5)

        # entries and their respective labels
        self.mid_frame = tk.Frame(self.master)
        self.yourName_lbl = tk.Label(self.mid_frame, text="Your name: ")
        self.yourName_lbl.grid(row=0, column=0, sticky='W')
        self.yourName_entry = tk.Entry(self.mid_frame)
        self.yourName_entry.grid(row=0, column=1)
        self.hostIP_lbl = tk.Label(self.mid_frame, text="Host's IP: ")
        self.hostIP_lbl.grid(row=1, column=0, sticky='W')
        self.hostIP_entry = tk.Entry(self.mid_frame)
        self.hostIP_entry.grid(row=1, column=1)
        self.mid_frame.pack(side=tk.TOP)

        # host and join buttons
        self.bot_frame = tk.Frame(self.master)
        self.btn_Host = tk.Button(self.bot_frame, text="Host Lobby", command = self.host)
        self.btn_Host.pack(side=tk.LEFT)
        self.btn_Join = tk.Button(self.bot_frame, text="Join Lobby", command = self.connect)
        self.btn_Join.pack(side=tk.LEFT)
        self.bot_frame.pack(side=tk.BOTTOM, pady=5)

    def host(self):
        name = self.yourName_entry.get()
        if not name:
            self.top_txt.configure(text="Please enter your name.")
        else:
            self.newWindow = tk.Toplevel(self.master)
            self.app = Lobby(self.newWindow, name, True)
            self.newWindow.grab_set()

    def connect(self):
        name = self.yourName_entry.get()
        hostIP = self.hostIP_entry.get()
        if not name:
            self.top_txt.configure(text="Please enter your name.")
            return
        if self.validateIP(hostIP):
            self.newWindow = tk.Toplevel(self.master)
            try:
                self.app = Lobby(self.newWindow, name, False, hostIP)
                self.newWindow.grab_set()
            except:
                self.top_txt.configure(text="Connection error.")
        else:
            self.top_txt.configure(text="Invalid IP.")

    def validateIP(self, ip):
        addr_vals = ip.split('.')
        if len(addr_vals) != 4:
            return False
        for val in addr_vals:
            if not val.isnumeric():
                return False
            val = int(val)
            if val > 255 or val < 0:
                return False
        return True





def main():
    root = tk.Tk()
    app = Q6nimmt(root)
    root.mainloop()

if __name__ == '__main__':
    main()
