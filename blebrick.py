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

class BLEBrick:

  def enableChannel(self, channel, useSmoothStart):
    return

  def isConnected(self):
    return False;

  def connect(self):
    return

  def disconnect(self):
      return

  def quickDrive(self, channel, direction, speed, duration):
    return

  def quickRun(self, *args):
    return

  def drive (self, channel):
    return

  def sendCommand(self, command):
    return
      
  def stop (self, channel="all"):
    return

  def readTemp(self):
    return

  def readVolt(self):
    return

  def readBrickId(self):
    return

  def twoDigitHex(self, number):
      return '%02x' % number

  def ReadSensors(self):
    return

  def setSpeed(self, channel, speed, useSmoothStart):
    return

  def setDirection(self, channel, direction):
    return

  def setDuration(self, channel, duration):
    return

  def getMaxSpeed(self):
    return 0
    
