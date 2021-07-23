#!/usr/bin/env python

# PPM.py
# 2016-02-18
# Public Domain
# Gotten from PIGPIOD

import inputs
import threading
import time
import pigpio

class X:

   GAP=300
   WAVES=3

   def __init__(self, pi, gpio, channels=8, frame_ms=27):
      # To pigpiod
      self.pi = pi
      # Pin to use
      self.gpio = gpio
      self.lock = threading.Lock()

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

      self._widths = [1000] * channels # set each channel to minimum pulse width

      self._wid = [None]*self.WAVES
      self._next_wid = 0

      pi.write(gpio, pigpio.LOW)

      self._update_time = time.time()

   def _update(self):
      wf =[]
      micros = 0
      for i in self._widths:
         wf.append(pigpio.pulse(0, 1<<self.gpio, self.GAP))
         wf.append(pigpio.pulse(1<<self.gpio, 0, i))
         micros += (i+self.GAP)
      # off for the remaining frame period
      wf.append(pigpio.pulse(0, 1<<self.gpio, self._frame_us-micros))

      self.pi.wave_add_generic(wf)
      wid = self.pi.wave_create()
      self.pi.wave_send_using_mode(wid, pigpio.WAVE_MODE_REPEAT_SYNC)
      self._wid[self._next_wid] = wid

      self._next_wid += 1
      if self._next_wid >= self.WAVES:
         self._next_wid = 0

      
      remaining = self._update_time + self._frame_secs - time.time()
      if remaining > 0:
         time.sleep(remaining)
      self._update_time = time.time()

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

   def cancel(self):
      self.pi.wave_tx_stop()
      for i in self._wid:
         if i is not None:
            self.pi.wave_delete(i)


"""
Enables USB event monitoring
Updates ppm signal every 10ms
   Update on every event will lag like crazy
"""
class Listener:
   def __init__(self, X):
      self.X = X
      self.stopf = False

      self.roll = 1225
      self.pitch = 1225
      self.throttle = 760
      self.yaw = 1225

      ## Reverse channels
      self.pitch_reverse = True
      self.roll_reverse = False
      self.yaw_reverse = False


   def start_listen(self):
      threading.Thread(target=self.read_dev, args=(0,)).start()
      threading.Thread(target=self.read_dev,args=(1,)).start()
      threading.Thread(target=self.update_channels).start()

   def stop(self):
      self.stopf = True
      exit()

   def update_channels(self):
      while not self.stopf:
         """self.X.update_channels([self.yaw, self.roll, self.pitch, self.throttle, 750, 750, 750]) """
         self.X.update_channels([760, self.roll, self.pitch, 760, self.yaw, 760, self.throttle])
         time.sleep(0.01)

   def read_dev(self, d):
      devices = inputs.DeviceManager()
      print("Listen:", d, devices.gamepads[d])
      thr = False
      if (str(devices.gamepads[d]) == "Madcatz Saitek Pro Flight X-55 Rhino Throttle"):
         thr = True
         print(d, "is thr")
      roll_d = False
      pitch_d = False
      yaw_d = False

      while not self.stopf:
         try:
            events = devices.gamepads[d].read()
            for event in events:
               if event.code == "ABS_Y":
                  if(thr):
                     self.set_throttle(event.state)
                  else:
                     self.set_pitch(event.state)
               elif event.code == "ABS_X":
                  if(not thr):
                     self.set_roll(event.state)
                  
               elif event.code == "ABS_RZ":
                  if(not thr):
                     self.set_yaw(event.state)
               
               ## If you want AUX channles to reverse, or add AUX buttons
               """#Reverse
               elif event.code == "BTN_TRIGGER_HAPPY3":
                  if not roll_d:
                     self.roll_reverse = not self.roll_reverse
                     print("Roll: ", self.roll_reverse)
                     roll_d = True
                  else:
                     roll_d = False
               elif event.code == "BTN_TRIGGER_HAPPY2":
                  if not pitch_d:
                     self.pitch_reverse = not self.pitch_reverse
                     print("Pitch: ", self.pitch_reverse)
                     pitch_d = True
                  else:
                     pitch_d = False
               elif event.code == "BTN_TRIGGER_HAPPY1":
                  if not yaw_d:
                     self.yaw_reverse = not self.yaw_reverse
                     print("Yaw: ", self.yaw_reverse)
                     yaw_d = True
                  else:
                     yaw_d = False """
         except:
            pass

   def set_roll(self, value):
      max_value = 65534
      x = ((value / max_value)*100)
      if self.roll_reverse:
         x = 100-x
      width =(int)(x * 9.5 + 750)
      self.roll = width
      
   def set_yaw(self, value):
      max_value = 4095
      x = (value / max_value)*100
      if self.yaw_reverse:
         x = 100-x
      width =(int)(x * 9.5 + 750)
      self.yaw = width

   def set_throttle(self, value):
      max_value = 1023
      x = (value / max_value)*100
      x = 100-x
      width =(int)(x * 9.5 + 700)
      self.throttle = width

   def set_pitch(self, value):
      max_value = 65534
      x = ((value / max_value)*100)
      if self.pitch_reverse:
         x = 100-x
      width =(int)(x * 9.5 + 750)
      self.pitch = width







if __name__ == "__main__":

   import time
   import PPM
   import pigpio
   pi = pigpio.pi()
   

   if not pi.connected:
      print("Not connected")
      exit(0)

   pi.wave_tx_stop() # Start with a clean slate.

   ppm = PPM.X(pi, 4, frame_ms=20)
   max_w = 1700
   min_w = 750
   initi = 1225
   ppm.update_channels([initi, initi, initi, initi, initi, initi, initi, initi])

   ls = PPM.Listener(ppm)
   ls.start_listen()

   inp = str(input())
   """ls.stop()"""
   time.sleep(0.2)
   ppm.cancel()
   ppm.stop()

   pi.stop()
   print("Bye")
   exit()