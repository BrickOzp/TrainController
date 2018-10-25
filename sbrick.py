#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright 2018 Oscar Rydhé

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from time import sleep
import thread
import threading
import time
from btledevice import BTLEDevice, NotConnectedError, NoResponseError
from Queue import Queue
from datetime import datetime
from blebrick import BLEBrick

class SBrick(BLEBrick):

  BREAK = '00'
  DRIVE = '01'

  lastSensorRead = 0

  def __init__(self, adapter, address, cb):
    self.bt_adapter = adapter
    self.bt_address = address
    self.handle = ''
    self.cb = cb

    print(' Adapter:    ', self.bt_adapter)
    print(' Device:     ', self.bt_address)

    self.connected = False

    self.CHANNEL_SPEED = [0, 0, 0, 0]

    self.CURRENT_CHANNEL_SPEED = [0, 0, 0, 0]

    self.CHANNEL_SMOOTH_START = [False, False, False, False]

    self.CHANNEL_DIRECTION = [False, False, False, False]
    
    self.CHANNEL_ENABLED = [False, False, False, False]
    
    self.CHANNEL_DURATION = [0, 0, 0, 0]

    self.highPrioMessages = Queue()

  def enableChannel(self, channel, useSmoothStart):
    self.CHANNEL_ENABLED[channel] = True
    self.CHANNEL_SMOOTH_START[channel] = useSmoothStart

  def isConnected(self):
    return self.connected

  def connect(self):
    if self.connected:
      print("Already connected")
      return
    
    thread.start_new_thread(self.onConnect, ());

  def disconnect(self):
    if not self.connected:
      print("Not connected")
      return

    self.connected = False
    self.CHANNEL_SPEED = [0, 0, 0, 0]
    self.CHANNEL_DIRECTION = [False, False, False, False]
    self.btledevice.stop()

  def onConnect(self):
    print("[{}] connect".format(self.bt_address))

    self.btledevice = BTLEDevice(self.bt_address, self.bt_adapter)
    try:
      self.btledevice.connect()
    except NotConnectedError:
      self.cb.onBLEBrickError(False)
      return
    
    try:
      self.SBRICK_HW_VS = self.btledevice.read(0x000C)
    except:
      print("[{}] Could not read sbrick hardware version".format(self.bt_address))
      self.cb.onBLEBrickError(True)
      return

    try:
      self.SBRICK_FW_VS = float(self.btledevice.read(0x000A))
    except:
      print("[{}] Could not read sbrick firmware version".format(self.bt_address))
      self.cb.onBLEBrickError(True)
      return

    print('[{}] bt_address Hw: {}'.format(self.bt_address, self.SBRICK_HW_VS))
    print('[{}] bt_address Fw: {}'.format(self.bt_address, self.SBRICK_FW_VS))

    if self.SBRICK_FW_VS == 4.0:
      print("Will use bt_address firmware 4.0 handles")
      print("Will limit values to 0..FE as FF doesn't work")
      self.handle = 0x0025
    elif (self.SBRICK_FW_VS >= 4.2 and self.SBRICK_FW_VS < 5) or \
        int(self.SBRICK_FW_VS == 5) or int(self.SBRICK_FW_VS == 11):
      print("Will use bt_address firmware 4.2+ handles")
      self.handle = 0x001A
    else:
      print("Don't know how to handle this firmware version")
      self.cb.onBLEBrickError(True)
      return

    self.btledevice.subscribe(self.handle, self.SensorUpdate)

    for channel in range(0, 4):
      if self.CHANNEL_SMOOTH_START[channel]:
        self.CURRENT_CHANNEL_SPEED[channel] = 0;

    self.connected = True
    self.cb.onBLEBrickConnected()
    self.thread = threading.Thread(target=self.Run)
    self.thread.start()
    #thread.start_new_thread(self.ReadSensors, ());

  def SensorUpdate(self, handle, value):
    v = (value[1] * 256 + value[0]) * 0.000378603
    t = (value[3] * 256 + value[2]) * 0.008413396 - 160
    self.cb.onBLEBrickSensorRead("{0:.1f}".format(v) + " V" + '/' + "{0:.1f}".format(t) + " °C");

  def quickDrive(self, channel, direction, speed, duration):
    thread.start_new_thread(self.quickRun, (channel, direction, speed, duration));

  def quickRun(self, *args):
        print(args)
        channel = args[0]
        direction = args[1]
        speed = args[2]
        duration = args[3]
        self.CHANNEL_DIRECTION[channel] = direction
        self.CHANNEL_SPEED[channel] = speed
        self.CURRENT_CHANNEL_SPEED[channel] = speed
        start_time = time.time()
        self.CHANNEL_ENABLED[channel] = False
        while True:
          self.drive(channel)
          remaining_duration = duration - (time.time() - start_time)
          #print(remaining_duration)
          if remaining_duration <= 0:
            break
          sleep(0.1 if remaining_duration > 0.1 else remaining_duration)
          if remaining_duration < 0:
            break
        self.stop(channel)
        self.CHANNEL_SPEED[channel] = 0
        self.CURRENT_CHANNEL_SPEED[channel] = 0
        self.CHANNEL_ENABLED[channel] = True

  def drive (self, channel):
    if self.CURRENT_CHANNEL_SPEED[channel] < self.CHANNEL_SPEED[channel]:
      if self.CURRENT_CHANNEL_SPEED == 0 and self.CHANNEL_SPEED[channel] > 80:
        self.CURRENT_CHANNEL_SPEED[channel] = 80
    
    self.sendCommand(self.DRIVE + self.twoDigitHex(channel) + ('01' if self.CHANNEL_DIRECTION[channel] else '00') + self.twoDigitHex(self.CURRENT_CHANNEL_SPEED[channel]))

    step = 20
    if self.CURRENT_CHANNEL_SPEED[channel] < self.CHANNEL_SPEED[channel]:
      self.CURRENT_CHANNEL_SPEED[channel] = self.CURRENT_CHANNEL_SPEED[channel] + (step if self.CHANNEL_SPEED[channel] - self.CURRENT_CHANNEL_SPEED[channel] > step else self.CHANNEL_SPEED[channel] - self.CURRENT_CHANNEL_SPEED[channel])
    elif self.CURRENT_CHANNEL_SPEED[channel] > self.CHANNEL_SPEED[channel]:
      self.CURRENT_CHANNEL_SPEED[channel] = self.CURRENT_CHANNEL_SPEED[channel] - (step if self.CURRENT_CHANNEL_SPEED[channel] - self.CHANNEL_SPEED[channel]  > step else self.CURRENT_CHANNEL_SPEED[channel] - self.CHANNEL_SPEED[channel])

  def sendCommand(self, command):
    #print("[{}] [{}] command: {}".format(datetime.now(), self.bt_address, command))
    try:
      self.btledevice.write(self.handle, command, True)
    except:
      print("Exception while writing")
      if self.connected:
        self.connected = False
        self.cb.onBLEBrickError(False)
      
  def stop (self, channel="all"):
    if self.connected:
      if channel == "all":
        self.sendCommand(self.BREAK + "00010203")
      else:
        self.highPrioMessages.put(self.BREAK + self.twoDigitHex(channel))

  def readTemp(self):
    unit = " °C"
    if self.SBRICK_FW_MINOR_VS >= 2:
      self.btledevice.write(self.handle, "0F0E", True)
      result = self.btledevice.read(self.handle)
      if len(result) == 2:
        t = (result[1] * 256 + result[0]) * 0.008413396 - 160

        return("{0:.1f}".format(t)+unit)

      # firmware 4.0 can't read temp/volt
    return("00.0"+unit)

  def readVolt(self):
    if self.SBRICK_FW_VS < 4.2:
      self.btledevice.write(self.handle, "0F00", True)
      result = self.btledevice.read(self.handle)
      if len(result) == 2:
        v = (result[1] * 256 + result[0]) * 0.000378603

        return("{0:.1f}".format(v)+" V")

    # firmware 4.0 can't read temp/volt
    return("0.0 V")

  def twoDigitHex(self, number):
      return '%02x' % number

  def Run(self):
    print("Thread started");
    while self.connected:
      while not self.highPrioMessages.empty():   
        self.sendCommand(self.highPrioMessages.get())
      for channel in range(0, 4):
        if self.CHANNEL_ENABLED[channel]:
          self.drive(channel);
      sleep(0.1);
    print("Thread ended");

  def ReadSensors(self):
    while self.connected:
      try:
        self.cb.onBLEBrickSensorRead(self.readVolt() + '/' + self.readTemp());
        sleep(2);
      except:
        pass

  def setSpeed(self, channel, speed, useSmoothStart):
    self.CHANNEL_SPEED[channel] = speed;
    if not useSmoothStart:
      self.CURRENT_CHANNEL_SPEED[channel] = speed;

  def setDirection(self, channel, direction):
    self.CHANNEL_DIRECTION[channel] = direction

  def setDuration(self, channel, duration):
    self.CHANNEL_DURATION[channel] = duration

  def getMaxSpeed(self):
    return 255
    
