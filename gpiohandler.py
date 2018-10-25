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

import RPi.GPIO as GPIO
from functools import partial
import datetime
import thread

class GPIOHandler:

    def __init__(self, xmlTag, trainController):

        self.trainController = trainController

        GPIO.setmode(GPIO.BOARD)

        self.ledon = False

        self.sensors = []

        for child in xmlTag:
            if child.tag == 'reed':
                rId = child.attrib['id']
                pin = int(child.attrib['pin'])
                self.sensors.append(rId)

                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=partial(self.detect, rId), bouncetime=500)

                print("GPIO setup in pin: " + str(pin))
            elif child.tag == 'light':
                rId = child.attrib['id']
                pin = int(child.attrib['pin'])
                self.sensors.append(rId)

                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(pin, GPIO.BOTH, callback=partial(self.detect, rId), bouncetime=200)

                print("GPIO setup in pin: " + str(pin))
                

    def detect(self, rId, pin):
        print("[{}] {}".format(datetime.datetime.now(), rId))

        #print(str(GPIO.input(pin)))
        
        thread.start_new_thread(self.distributeDetect, (rId,));

    def distributeDetect(self, *args):
        self.trainController.sensorDetected(args[0])

    def getSensors(self):
        return self.sensors

    def destroy(self):
        print("destroy")
        GPIO.cleanup()
