import tkinter as tk

# gui for selecting which operation to modify the discarded card
class OpsSelection(tk.Frame):
    def __init__(self, master, ops=["(none)", "H", "Z"], mqops=["CNot", "hSwap"]):
        tk.Frame.__init__(self, master)
        self.ops = ops
        self.mqops = mqops
        self.selectedOp = tk.StringVar()
        self.generateButtons()

    def generateButtons(self):
        self.opButtons = []
        self.mqopButtons = []

        # dummy command for testing purposes
        # def showChoice():
        #     print(self.selectedOp.get())

        # label and generate single qubit operations
        self.opsFrame = tk.Frame(self)
        self.opsLabel = tk.Label(self.opsFrame, text="Ops")
        self.opsLabel.pack(side=tk.TOP)
        for op in self.ops:
            op_button = tk.Radiobutton(self.opsFrame, text=op, indicatoron=0, width=5, bg="#CCCCCC",
                                      # command=showChoice,
                                      variable=self.selectedOp, value=op)
            op_button.pack(side=tk.TOP)
            self.opButtons.append(op_button)
        self.opsFrame.pack(side=tk.TOP)

        # label and generate two-qubit operations
        self.mqopsFrame = tk.Frame(self)
        self.mqopsLabel = tk.Label(self.mqopsFrame, text="MQ Ops")
        self.mqopsLabel.pack(side=tk.TOP)
        for mqop in self.mqops:
            mqop_button =tk.Radiobutton(self.mqopsFrame, text=mqop, indicatoron=0, width=7, bg="#FFFFCC",
                           # command=showChoice,
                           variable=self.selectedOp, value=mqop)
            mqop_button.pack(side=tk.TOP)
            self.mqopButtons.append(mqop_button)
        self.mqopsFrame.pack(side=tk.TOP)

    def disableMqops(self):
        for button in self.mqopButtons:
            button.config(state="disabled", bg="#FFAAAA", fg="#000000", text="N/A")
        self.opButtons[0].select()

    def enableMqops(self):
        for button, op in zip(self.mqopButtons, self.mqops):
            button.config(state="normal", bg="#FFFFCC", fg="#000000", text=op)


def opsTest():
    root = tk.Tk()
    opsbox = OpsSelection(root)
    opsbox.pack()
    def testEnable():
        opsbox.enableMqops()
    def testDisable():
        opsbox.disableMqops()
        root.after(5000, testEnable)
    root.after(5000, testDisable)
    root.mainloop()

if __name__ == '__main__':
    opsTest()
