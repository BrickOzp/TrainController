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

class PFxBrick(BLEBrick):
  def __init__(self, adapter, address, cb):
    self.bt_adapter = adapter
    self.bt_address = address
    self.handle = 0x0055
    self.cb = cb

    print(' Adapter:    ', self.bt_adapter)
    print(' Device:     ', self.bt_address)

    self.connected = False

    self.CHANNEL_SPEED = [0, 0, 0, 0]

    self.CURRENT_CHANNEL_SPEED = [0, 0, 0, 0]

    self.LAST_WRITTEN_CHANNEL_SPEED = [0, 0, 0, 0]

    self.CHANNEL_SMOOTH_START = [False, False, False, False]

    self.CHANNEL_DIRECTION = [False, False, False, False]
    
    self.CHANNEL_ENABLED = [False, False, False, False]
    
    self.CHANNEL_DURATION = [0, 0, 0, 0]

    self.commandQueue = Queue()

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
      self.PFXBRICK_MODEL_NO = self.btledevice.read(0x0014)
    except:
      print("[{}] Could not read PFxbrick model number".format(self.bt_address))
      self.cb.onBLEBrickError(True)
      return

    print('[{}] PFxBrick Model number: {}'.format(self.bt_address, self.PFXBRICK_MODEL_NO))

    for channel in range(1, 3):
      if self.CHANNEL_SMOOTH_START[channel]:
        self.CURRENT_CHANNEL_SPEED[channel] = 0;
      self.LAST_WRITTEN_CHANNEL_SPEED[channel] = 0

    self.connected = True
    self.cb.onBLEBrickConnected()
    self.thread = threading.Thread(target=self.Run)
    self.thread.start()

  def quickDrive(self, channel, direction, speed, duration):
    self.commandQueue.put('13008' + str(channel) + hex(0xBF + (0x40 if direction else 0x00))[2:4] + '02000000000000000000000000')

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
      if self.CURRENT_CHANNEL_SPEED == 0 and self.CHANNEL_SPEED[channel] > 20:
        self.CURRENT_CHANNEL_SPEED[channel] = 20

    self.LAST_WRITTEN_CHANNEL_SPEED[channel] = self.CURRENT_CHANNEL_SPEED[channel]
    self.sendCommand('13007' + str(channel) + hex(0x80 + (0x40 if self.CHANNEL_DIRECTION[channel] else 0x00) + self.CURRENT_CHANNEL_SPEED[channel])[2:4] + '00000000000000000000000000')

    step = 5
    if self.CURRENT_CHANNEL_SPEED[channel] < self.CHANNEL_SPEED[channel]:
      self.CURRENT_CHANNEL_SPEED[channel] = self.CURRENT_CHANNEL_SPEED[channel] + (step if self.CHANNEL_SPEED[channel] - self.CURRENT_CHANNEL_SPEED[channel] > step else self.CHANNEL_SPEED[channel] - self.CURRENT_CHANNEL_SPEED[channel])
    elif self.CURRENT_CHANNEL_SPEED[channel] > self.CHANNEL_SPEED[channel]:
      self.CURRENT_CHANNEL_SPEED[channel] = self.CURRENT_CHANNEL_SPEED[channel] - (step if self.CURRENT_CHANNEL_SPEED[channel] - self.CHANNEL_SPEED[channel]  > step else self.CURRENT_CHANNEL_SPEED[channel] - self.CHANNEL_SPEED[channel])

  def sendCommand(self, command):
    #print("[{}] [{}] command: {}".format(datetime.now(), self.bt_address, command))

    try:
      if len(command) < 20:
        print("Not implemented")
      else:
        send_command = '5B5B5B' + command[0:26]
        self.btledevice.write(self.handle, send_command, True)
        send_command = '' + command[26:len(command)] + '5D5D5D'
        self.btledevice.write(self.handle, send_command, True)
    except:
      print("Exception while writing")
      if self.connected:
        self.connected = False
        self.cb.onBLEBrickError(False)
      
  def stop (self, channel="all"):
    if self.connected:
      if channel == "all":
        self.commandQueue.put('13001F00000000000000000000000000')
      else:
        self.commandQueue.put('13001' + str(channel) + '00000000000000000000000000')

  def twoDigitHex(self, number):
      return '%02x' % number

  def Run(self):
    print("Thread started");
    while self.connected:
      commandSent = False
      while not self.commandQueue.empty():   
        self.sendCommand(self.commandQueue.get())
        commandSent = True
      for channel in range(1, 3):
        if self.CHANNEL_ENABLED[channel]:
          if self.LAST_WRITTEN_CHANNEL_SPEED[channel] != self.CHANNEL_SPEED[channel]:
            self.drive(channel);
            commandSent = True
      if not commandSent:
        sleep(0.1)
    print("Thread ended");

  def setSpeed(self, channel, speed, useSmoothStart):
    self.CHANNEL_SPEED[channel] = speed;
    if not useSmoothStart:
      self.CURRENT_CHANNEL_SPEED[channel] = speed;

  def setDirection(self, channel, direction):
    self.CHANNEL_DIRECTION[channel] = direction

  def setDuration(self, channel, duration):
    self.CHANNEL_DURATION[channel] = duration

  def getMaxSpeed(self):
    return 63
    
