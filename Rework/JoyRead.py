import sys
import os
import threading
from time import sleep
from time import time
import inputs
import pigpio


class JoyRead:
    def __init__(self, sg, joy_name, thr_name, joy_max, thr_max):
        self.sg = sg
        self.ppm = None
        

        self.devices = inputs.DeviceManager()
        # TODO: Support pedals
        self.joy = joy_name
        self.thr = thr_name
        self.max = joy_max
        self.max.update(thr_max)
        self.update_delay = 0.01 # Secs

        self.listening = True

        # TODO: Change this
        self.code_to_chan = {"ABS_Y": 2,
            "ABS_X": 1, "ABS_RZ": 4, "THR_ABS_Y": 3}

    def update_chan(self, event, dev):
        code = event.code
        if str(dev) == str(self.thr):
            code = "THR_"+code

        if code in self.code_to_chan.keys():
            if code == "THR_ABS_Y":
                perc = 100 - (event.state // (self.max[code] / 100))
            else:
                perc = event.state // (self.max[code] / 100)
            self.sg.set_channel_perc(self.code_to_chan[code], perc)

    def listen(self, dev):
        idx = -1
        for i, x in enumerate(self.devices.gamepads):
            if str(dev) == str(x):
                idx = i
        if idx == -1:
            print("oof")
            return
        while self.listening:
            try:
                for event in self.devices.gamepads[idx].read():
                    self.update_chan(event, dev)
            except:
                continue


    def start_listen(self):
        threading.Thread(target=self.listen, args=(self.joy,)).start()
        threading.Thread(target=self.listen, args=(self.thr,)).start()

    def start_wave(self):
        pi = pigpio.pi()
        if not pi.connected:
            print("Not connected")
            return -1

        pi.wave_tx_stop()  # Start with a clean slate.

        self.ppm = PPM(pi, 4, frame_ms=20)

        self.ppm.update_channels_perc(self.sg.channels_perc)
        threading.Thread(target=self._start_updates).start()
        return 0
    
    def _start_updates(self):
        while self.listening:
            self.ppm.update_channels_perc(self.sg.channels_perc)
            sleep(self.update_delay)


def setup_joy():

    max_values_joy = dict()
    max_values_thr = dict()
    joy_name = ""
    thr_name = ""

    if os.path.exists("joy_config.cfg"):
        with open("joy_config.cfg", "r") as f:
            joy_name = f.readline().strip()
            thr_name = f.readline().strip()
            for l in f:
                parts = l.split(";")
                if "THR" in parts[0]:
                    max_values_thr[parts[0]] = int(parts[1])
                else:
                    max_values_joy[parts[0]] = int(parts[1])

    else:
        devices = inputs.DeviceManager()

        # TODO: Terminate
        if (len(devices.gamepads) < 2):
            print("Need throttle and joystick")

        print("Select joystick:")
        for i, dev in enumerate(devices.gamepads):
            print(str(i)+": "+str(dev))
        joy_idx = -1
        while (0 > joy_idx or (joy_idx >= len(devices.gamepads))):
            try:
                joy_idx = int(input("Index: "))
            except:
                continue

        # Only codes i care about
        codes = ["ABS_Y", "ABS_X", "ABS_RZ"]

        print("Move the joystick to all min/max values (You have 10 seconds)")

        start = time()
        while (time()-start) < 10:
            try:
                for event in devices.gamepads[joy_idx].read():
                    # Only read abs
                    if event.code not in codes:
                        continue
                    if event.code in max_values_joy.keys():
                        if max_values_joy[event.code] < event.state:
                            max_values_joy[event.code] = event.state
                    else:
                        max_values_joy[event.code] = event.state
            except:
                continue
        print(str(max_values_joy))

        print("Select throttle:")
        for i, dev in enumerate(devices.gamepads):
            if i == joy_idx:
                continue
            print(str(i)+": "+str(dev))

        thr_idx = -1
        while 0 > thr_idx or thr_idx >= len(devices.gamepads):
            try:
                thr_idx = int(input("Index: "))
            except:
                continue
            if thr_idx == joy_idx:
                thr_idx = -1

        print("Move the throttle from 0 to max (5 seconds)")
        start = time()

        while (time()-start) < 5:
            try:
                for event in devices.gamepads[thr_idx].read():
                    # Only read abs
                    if event.code not in codes:
                        continue
                    if event.code in max_values_thr.keys():
                        if max_values_thr[event.code] < event.state:
                            max_values_thr[event.code] = event.state
                    else:
                        max_values_thr[event.code] = event.state
            except:
                continue
        for x in [x for x in max_values_thr.keys()]:
            max_values_thr["THR_"+x] = max_values_thr[x]
            del max_values_thr[x]

        print(str(max_values_thr))

        joy_name = str(devices.gamepads[joy_idx])
        thr_name = str(devices.gamepads[thr_idx])

        if input("Would you like to save this configuration? (Y/N)  ") == "Y":
            with open("joy_config.cfg", "w") as f:
                f.write(joy_name)
                f.write("\n")
                f.write(thr_name)

                s = ""
                for key in max_values_joy.keys():
                    f.write("\n")
                    f.write(key+";"+str(max_values_joy[key]))
                for key in max_values_thr.keys():
                    f.write("\n")
                    f.write(key+";"+str(max_values_thr[key]))

    sg = SignalValues(7, throttle=3)

    return JoyRead(sg, joy_name, thr_name, max_values_joy, max_values_thr)


# SignalValues


class SignalValues:
    def __init__(self, n, throttle=0, dead_zone=2):
        self.n_channels = n
        self.throttle = throttle
    
        # TODO: Add values
        self.min_value = 750
        self.max_value = 1700
        self.net_value = (self.max_value+self.min_value) // 2

        self.channels_val = [self.net_value]*self.n_channels
        self.channels_perc = [50] * self.n_channels
        self.channels_val[throttle] = 0
        self.channels_perc[throttle] = 0
        self.th = None
        self.done = False

    def set_channel_perc(self, chan, perc):
        if (0 > perc > 100):
            return -1
        
        # Dead zone
        if chan != self.throttle:
            if 48 < perc < 52:
                perc = 50
        else:
            if 98 <= perc:
                perc = 100
            elif 2 >= perc:
                perc = 0



        new_val = ((self.max_value / 100) * perc) // 1

        self.channels_val[chan] = new_val
        self.channels_perc[chan] = perc
        return 0


    # Unused
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
        lables = [tk.Label(frame, text="Channel "+str(i+1), padx=10)
                  for i, frame in enumerate(frames)]
        scales = [tk.Scale(frame, from_=100, to=0) for frame in frames]

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


class PPM:

   GAP = 300
   WAVES = 3

   def __init__(self, pi, gpio, channels=8, frame_ms=20):
      # To pigpiod
      self.pi = pi
      # Pin to use
      self.gpio = gpio
      self.lock = threading.Lock()

      self.max_val = 1700
      self.min_val = 750

      if frame_ms < 5:
         frame_ms = 5
         channels = 2
      elif frame_ms > 100:
         frame_ms = 100

      self.frame_ms = frame_ms

      self._frame_us = int(frame_ms * 1000)
      self._frame_secs = frame_ms / 1000.0

      if channels < 1:
         channels = 1
      elif channels > (frame_ms // 2):
         channels = int(frame_ms // 2)

      self.channels = channels

      # set each channel to minimum pulse width
      self._widths = [1050] * channels

      self._wid = [None]*self.WAVES
      self._next_wid = 0

      pi.write(gpio, pigpio.LOW)

      self._update_time = time()

   def _update(self):
      wf = []
      micros = 0
      for i in self._widths:
         wf.append(pigpio.pulse(0, 1 << self.gpio, self.GAP))
         wf.append(pigpio.pulse(1 << self.gpio, 0, i))
         micros += (i+self.GAP)
      # off for the remaining frame period
      wf.append(pigpio.pulse(0, 1 << self.gpio, self._frame_us-micros))

      self.pi.wave_add_generic(wf)
      wid = self.pi.wave_create()
      self.pi.wave_send_using_mode(wid, pigpio.WAVE_MODE_REPEAT_SYNC)
      self._wid[self._next_wid] = wid

      self._next_wid += 1
      if self._next_wid >= self.WAVES:
         self._next_wid = 0

      remaining = self._update_time + self._frame_secs - time()
      if remaining > 0:
         sleep(remaining)
      self._update_time = time()

      wid = self._wid[self._next_wid]
      if wid is not None:
         self.pi.wave_delete(wid)
         self._wid[self._next_wid] = None

   def update_channel(self, channel, width):
      self._widths[channel] = width
      self._update()

   def update_channels(self, widths):
      self._widths[0:len(widths)] = widths[0:self.channels]
      self._update()


   def update_channels_perc(self, percentages):
        widths = [int(((((self.max_val-self.min_val)/100)*x)+self.min_val)) for x in percentages]
        self._widths[0:len(widths)] = widths[0:self.channels]
        self._update()

   def cancel(self):
      self.pi.wave_tx_stop()
      for i in self._wid:
         if i is not None:
            self.pi.wave_delete(i)



if __name__ == "__main__":
    joy = setup_joy()
    joy.start_listen()
    if len(sys.argv) == 2:
        joy.sg.show_plot()  

    if len(sys.argv) == 1:
        print("Starting wave")
        if joy.start_wave() == -1:
            # joy.sg.kill_window()
            if (joy.ppm != None):
                joy.ppm.cancel()
            print("OOF")
            joy.listening = False
            exit()

    

    input()
    if len(sys.argv) == 2:
        joy.sg.kill_window()
    if (joy.ppm != None):
        joy.ppm.cancel()
    joy.listening = False
