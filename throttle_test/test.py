import inputs
import threading
import time

def main():

   threading.Thread(target=read_dev, args=(0,)).start()
   threading.Thread(target=read_dev,args=(1,)).start()
   """Just print out some event infomation when the gamepad is used.
    devices = inputs.DeviceManager()
    while 1:
         events = devices.gamepads[0]._do_iter()
         events2 = devices.gamepads[1]._do_iter()
         r = True
         x = 0
         y = 0
         while r:
            if len(events) >= x:
               event = events[x]
               print(event.ev_type, event.code, event.state)
            if len(events2) >= y:
               event = events2[y]
               print(event.ev_type, event.code, event.state)
            y = y+1
            x = x+1
            if len(events2) >= y and len(events) >= x:
               r = False
"""
""" 0 = thr, 1 = joy """
def read_dev(d):
   devices = inputs.DeviceManager()
   while 1:
      try:
         events = devices.gamepads[d].read()
         for event in events:
            if event.code == "ABS_Y":
               if(d == 0):
                  set_throttle(event.state)
               else:
                  set_pitch(event.state)
            elif event.code == "ABS_X":
               if(d == 1):
                  set_roll(event.state)
               
            elif event.code == "ABS_RZ":
               if(d == 1):
                  set_yaw(event.state)
                   
      except:
         pass

def set_roll(value):
   channel = 0
   max_value = 65534
   x = (value / max_value)*100
   width =(int)(x * 9.5 + 750)
   print("Roll:", x)
   """ update_channel(channel, width) """

   
def set_yaw(value):
   channel = 0
   max_value = 4095
   x = (value / max_value)*100
   width =(int)(x * 9.5 + 750)
   print("Yaw:", x)

def set_throttle(value):
   channel = 1
   max_value = 1023
   x = (value / max_value)*100
   width =(int)(x * 9.5 + 750)
   print("Thr:", x)

def set_pitch(value):
   channel = 0
   max_value = 65534
   x = (value / max_value)*100
   width =(int)(x * 9.5 + 750)
   print("Pitch:", x)

if __name__ == "__main__":
    main()