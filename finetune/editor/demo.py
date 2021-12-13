import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk

window=tk.Tk()
window.title("IPES Graphing Tool")
window.geometry('1150x840')

plot_frame = tk.Frame(window)
plot_frame.pack(side = tk.TOP,padx=5,pady=5)

fig1=Figure(figsize=(9,7))
ax= fig1.add_axes([0.1,0.1,0.65,0.75])

canvas = FigureCanvasTkAgg(fig1, window)
canvas.get_tk_widget().pack(padx=20,side=tk.TOP, fill=tk.BOTH, expand=False)
toolbar = NavigationToolbar2Tk(canvas, window)
toolbar.update()

def choose_cords(draw):
    draw.cid=canvas.mpl_connect('button_press_event', draw.get_cords)

class DrawLine: # a simple class to store previous cords
    def __init__(self):
        self.x = None
        self.y = None
        self.cid = None

    def get_cords(self, event):
        if self.x and self.y:
            ax.plot([self.x, event.xdata], [self.y, event.ydata])
            canvas.draw_idle()
            canvas.mpl_disconnect(self.cid)
            self.__init__()
            return
        self.x, self.y = event.xdata, event.ydata

draw = DrawLine()
draw_btn = tk.Button(window, text="Draw the Line", command=lambda:choose_cords(draw)).pack(side=tk.TOP,padx=5,pady=5)

window.mainloop()