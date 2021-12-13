from tkinter import *
import tkinter.ttk  as ttk 

class MainApp(ttk.Notebook):
    def __init__(self, root=None, **args):
        args.setdefault('height', 600)
        args.setdefault('width', 800)
        ttk.Notebook.__init__(self, master=root, **args)


if __name__ == '__main__':
    app = MainApp()
    app.mainloop()