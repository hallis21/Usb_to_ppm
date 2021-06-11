import inputs
import SignalValues


class JoyRead:
    def __init__(self, sg :SignalValues):
        self.sg = sg

        self.devices = inputs.DeviceManager()
        self.joy = 0
        self.thr = 1


        self.code_to_chan = {"ABS_Y":0 , "ABS_X":1, "ABS_RZ":2}

        
    def get_prec(self, event):
        


    def update_chan(self, event, dev):
        if dev != self.joy:
            if event.code == "ABS_Y":
                self.sg.set_channel_perc()
        else:
            if event.code == "ABS_Y":
                pass



    def choose_dev(self):
        pass
