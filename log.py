import tkinter as tk
from tkinter import scrolledtext
import time

class Log(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        self.textBox = scrolledtext.ScrolledText(self, height=7)
        self.textBox.grid(sticky='news')
        self.textBox.config(state="disabled")

    def display(self, text):
        self.textBox.config(state="normal")
        self.textBox.insert(tk.END, text + '\n')
        self.textBox.see(tk.END)
        self.textBox.config(state="disabled")


def logTest():
    root = tk.Tk()
    textbox = Log(root)
    textbox.pack()
    x = 0
    def displayTest():
        nonlocal x
        textbox.display(str(x))
        x += 1
        root.after(2000, displayTest)
    root.after(2000, displayTest)
    root.mainloop()


if __name__ == '__main__':
    logTest()