#!/usr/bin/python
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

import thread
from time import sleep
import datetime
import time

class SingeTrackScenario:

    def __init__(self, trains, sensors, switchGroups, switchIndex):
        print("SingeTrackScenario init");
        print(trains)
        print(sensors)
        print(switchGroups)
        print(switchIndex)
        self.trains = trains
        self.sensors = sensors
        self.switchGroups = switchGroups
        self.switchIndex = switchIndex
        self.speeds = [0] * 4

        for i in range(4):
            if trains[i] is None:
                self.toTrack = i

        if self.toTrack == 0 or self.toTrack == 1:
            self.fromTrack = 2
        else:
            self.fromTrack = 0

        self.startNextTrain()

    def findNextTrain(self):
        emptyTrack = self.fromTrack

        if self.toTrack == 0:
            self.fromTrack = 1
        elif self.toTrack == 1:
            self.fromTrack = 0
        elif self.toTrack == 2:
            self.fromTrack = 3
        elif self.toTrack == 3:
            self.fromTrack = 2

        self.toTrack = emptyTrack

    def startNextTrain(self):
        print("startNextTrain from: {} to: {}".format(self.fromTrack, self.toTrack))
        self.currentTrain = self.trains[self.fromTrack]
        self.trains[self.fromTrack] = None
        self.expectingSensor = self.sensors[self.toTrack]

        if self.fromTrack == 0 or self.toTrack == 0:
            switchLeft = True
        elif self.fromTrack == 1 or self.toTrack == 1:
            switchLeft = False
        if self.switchGroups[0].getDirection(self.switchIndex[0]) == 'left':
            self.switchGroups[0].setSwitch(self.switchIndex[0], switchLeft)
        else:
            self.switchGroups[0].setSwitch(self.switchIndex[0], not switchLeft)

        if self.fromTrack == 2 or self.toTrack == 2:
            switchLeft = False
        elif self.fromTrack == 3 or self.toTrack == 3:
            switchLeft = True
        if self.switchGroups[1].getDirection(self.switchIndex[1]) == 'left':
            self.switchGroups[1].setSwitch(self.switchIndex[1], switchLeft)
        else:
            self.switchGroups[1].setSwitch(self.switchIndex[1], not switchLeft)

        sleep(1)

        speed = self.speeds[self.fromTrack]
        self.currentTrain.setSpeed(100 if speed == 0 else speed, True)        

    def sensorDetected(self, rId):
        if rId == self.expectingSensor:
            print("[{}] {} detected SingeTrackScenario".format(time.time(), self.expectingSensor));

            thread.start_new_thread(self.stopTrain, ());

    def stopTrain(self, *args):
    
        speed = self.train.getSpeed()

        self.speeds[self.toTrack] = speed

        self.currentTrain.onStop()

        self.currentTrain.toggleDirection()

        self.trains[self.toTrack] = self.currentTrain

        self.findNextTrain()

        self.startNexTrain()

    def stopScenario(self):
        self.currentTrain.onStop()

        self.expectingSensor = None
        
