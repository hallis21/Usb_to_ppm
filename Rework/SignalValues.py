
import threading    
from time import sleep


class SignalValues:
    def __init__(self, n, throttle=0):
        self.n_channels = n  
        self.throttle = throttle
        # TODO: Add values
        self.min_value = 0  
        self.max_value = 100
        self.net_value = self.max_value // 2

        self.channels_val = [self.net_value for x in range(self.n_channels)]
        self.channels_perc = [50 for x in range(self.n_channels)]
        self.channels_val[throttle] = 0
        self.channels_perc[throttle] = 0
        self.th = None
        self.done = False

    def set_channel_perc(self, chan, perc):
        if (0 > perc > 100):
            return -1
        
        new_val = ((self.max_value / 100) * perc) // 1

        self.channels_val[chan] = new_val
        self.channels_perc[chan] = perc
        return 0


    def set_channel_val(self, chan, val):
        if (self.min_value > val > self.max_value):
            return -1
        
        self.channels_val[chan] = val
        new_val = ((self.max_value / 100) // val) // 1
        self.channels_perc[chan] = new_val
        return 0



    def _show_plot(self):
        import tkinter as tk
        window = tk.Tk()


        frames = [tk.Frame(window) for _ in self.channels_perc]

        # Create sliders
        lables = [tk.Label(frame, text="Channel "+str(i+1), padx=10) for i, frame in enumerate(frames)]
        scales = [tk.Scale(frame,from_=100, to=0) for frame in frames]

        

        [x.pack() for x in lables]
        [x.pack() for x in scales]

        [x.pack(side=tk.LEFT) for x in frames]


        def tset():
            [x.set(self.channels_perc[i]) for i, x in enumerate(scales)]


            if (self.done):
                window.destroy()
                return
            window.after(10, tset)

        tset()
        window.mainloop()

    def show_plot(self):
        self.th = threading.Thread(target=self._show_plot)
        self.th.start()


       
    def kill_window(self):
        self.done = True
        if self.th != None:
            self.th.join()

