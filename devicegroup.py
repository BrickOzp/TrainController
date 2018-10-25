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

import Tkinter as ttk
from blebrick import BLEBrick
from sbrick import SBrick
from pfxbrick import PFxBrick
from functools import partial
from pydoc import locate
import sys

class Port:

    blebrick = 0
    channel = 0
    inverted = False

    def __init__(self, blebrick, channel, inverted, useSmoothStart, name, event):
        self.blebrick = blebrick
        self.channel = channel
        self.inverted = inverted
        self.name = name
        self.event = event

        blebrick.enableChannel(channel, useSmoothStart)

    def setSpeed(self, speed, useSmoothStart = False):
        self.blebrick.setSpeed(self.channel, speed, useSmoothStart)

    def setDirection(self, direction):
        if self.inverted:
            self.blebrick.setDirection(self.channel, not direction)
        else:
            self.blebrick.setDirection(self.channel, direction)

    def stop(self):
        self.blebrick.stop(self.channel)

class DeviceGroup:

    enabled = 0
    directions = []
    speed = 0
    blebrick = 0

    def __init__(self, xmlTag, ttkRoot, col, row):
        sys.path.append('./event')
        
        self.name = xmlTag.attrib['name']

        self.connectedTo = None
        self.connectedTrains = []
        self.eventClasses = []

        self.parseConfig(xmlTag)

        container = ttk.LabelFrame(ttkRoot)
        container.grid(row=row,column=col, sticky='n', padx=5, pady=5)

        row1 = ttk.Frame(container)
        row1.pack(fill="x", padx=5);

        self.enabled = ttk.BooleanVar()
        enableChk = ttk.Checkbutton(row1, variable=self.enabled, command=self.onEnable);
        enableChk.pack(side=ttk.LEFT);

        self.statusLbl = ttk.Label(row1, text="disabled")
        self.statusLbl.pack(side=ttk.RIGHT);

        name = ttk.Label(row1, text=self.name)
        name.pack();

        self.speeds = []
        self.speedScales = []
        self.stopButtons = []
        self.eventButtons = []
        for motor in self.motors:
            rowTitle = ttk.Frame(container)
            rowTitle.pack(fill="x", pady=5, padx=5);

            title = ttk.Label(rowTitle, text=motor.name)
            title.pack()
            
            row2 = ttk.Frame(container)
            row2.pack(fill="x", pady=5, padx=5);

            speed = ttk.IntVar()
            speedScale = ttk.Scale(row2, from_=0, to=self.blebrick.getMaxSpeed(), length=180,
               orient=ttk.HORIZONTAL, variable=speed, state=ttk.DISABLED, command=partial(self.onSpeedChanged, len(self.speedScales)))
            speedScale.pack(side=ttk.LEFT)
            self.speedScales.append(speedScale)
            self.speeds.append(speed)

            if motor.event is not None:
                eventBtn = ttk.Button(row2, text="E", state=ttk.DISABLED, command=partial(self.onEventLoad, len(self.eventButtons)))
                eventBtn.pack(side=ttk.LEFT, padx=5, pady=5)
                self.eventButtons.append(eventBtn)
            else:
                self.eventButtons.append(None)
            self.eventClasses.append(None)

            stopBtn = ttk.Button(row2, text="STOP", bg="red", activebackground="red",
                state=ttk.DISABLED, command=partial(self.onStop, len(self.stopButtons)))
            stopBtn.pack(side=ttk.RIGHT, padx=5, pady=5)
            self.stopButtons.append(stopBtn)

        row3 = ttk.Frame(container)
        row3.pack(fill="x", padx=5);

        self.stopAllBtn = ttk.Button(row3, text="STOP ALL", bg="red", activebackground="red",
            state=ttk.DISABLED, command=self.onStopAll)
        self.stopAllBtn.pack(side=ttk.RIGHT, padx=5, pady=5)

        self.eventBtn = None
        if self.event_class_name is not None:
            self.eventBtn = ttk.Button(row3, text="E", state=ttk.DISABLED, command=self.onEventLoad)
            self.eventBtn.pack(side=ttk.LEFT)

    def parseConfig(self, xmlTag):
        self.motors = []
        self.lights = []
        self.event_class_name = None

        for child in xmlTag:
            if child.tag == 'sbrick':
                address = child.attrib['address']

                if self.blebrick is not 0:
                    raise Error('Only one BLEBrick is supported per train')
                
                sbrick = SBrick('hci0', address, self)
                self.blebrick = sbrick

                for channel in child:
                    if channel.tag == 'channel':
                        cId = channel.attrib['id']
                        service = channel.attrib['service']
                        name = channel.attrib['name']

                        event = None
                        if 'event' in channel.attrib:
                            event = channel.attrib['event']

                        if service == 'motor':
                            inverted = 'false'
                            if 'inverted' in channel.attrib:
                                inverted = channel.attrib['inverted']
                            self.motors.append(Port(sbrick, int(cId), inverted == 'true', True, name, event))
            elif child.tag == 'pfxbrick':
                address = child.attrib['address']
                
                if self.blebrick is not 0:
                    raise Error('Only one BLEBrick is supported per train')

                pfxbrick = PFxBrick('hci0', address, self)
                self.blebrick = pfxbrick

                for channel in child:
                    if channel.tag == 'channel':
                        cId = channel.attrib['id']
                        service = channel.attrib['service']
                        name = channel.attrib['name']
                        event = channel.attrib['event']

                        if service == 'motor':
                            inverted = 'false'
                            if 'inverted' in channel.attrib:
                                inverted = channel.attrib['inverted']
                            self.motors.append(Port(pfxbrick, int(cId), inverted == 'true', True, name, event))
            elif child.tag ==  'event':
                self.event_class_name = child.attrib['class_name']

    #def stop(self):
    #    self.sbrick.disconnect()

    def onEnable(self):
       
        if self.enabled.get():
            self.blebrick.connect()
            self.statusLbl.config(text="connecting...", fg="black");
            i = 0
            for motor in self.motors:
                self.speedScales[i].config(state='normal')
                self.stopButtons[i].config(state='normal')
                if self.eventButtons[i] is not None:
                    self.eventButtons[i].config(state='normal')
                i = i + 1
            self.stopAllBtn.config(state='normal')
            if self.eventBtn is not None:
                self.eventBtn.config(state='normal')
        else:
            self.blebrick.disconnect()
            i = 0
            for motor in self.motors:
                self.speedScales[i].config(state='disabled')
                self.stopButtons[i].config(state='disabled')
                if self.eventButtons[i] is not None:
                    self.eventButtons[i].config(state='disabled')
                self.speeds[i].set(0)
                i = i + 1
            self.stopAllBtn.config(state='disabled')
            self.statusLbl.config(text="disabled", fg="black")
            if self.eventBtn is not None:
                self.eventBtn.config(state=ttk.DISABLED, relief=ttk.RAISED)

    def onStop(self, index):
        self.speeds[index].set(0)

        self.motors[index].setSpeed(0)

        self.motors[index].stop()

    def onStopAll(self):
        for i in range(0, len(self.motors)):
            self.onStop(i)
            
    def onSpeedChanged(self, index, val):
        self.motors[index].setSpeed(self.speeds[index].get())

    def onEventLoad(self, index):
        if self.eventClasses[index] is None:
            self.eventButtons[index].config(relief=ttk.SUNKEN)
            clazz = locate(self.motors[index].event, 1)
            self.eventClasses[index] = clazz(self, index)
        else:
            self.eventClasses[index].stop()
            self.eventButtons[index].config(relief=ttk.RAISED)
            self.eventClasses[index] = None

    def onBLEBrickError(self, fatal):
        if self.enabled.get():
            self.statusLbl.config(text="Error", fg="red");
            if not fatal:
                self.blebrick.connect()

    def onBLEBrickConnected(self):
        self.statusLbl.config(text="connected", fg="black");
        for motor in self.motors:
            motor.setDirection(True)
                               
    def onBLEBrickSensorRead(self, val):
        self.statusLbl.config(text=val, fg="black");

    def getName(self):
        return self.name

    def isEnabled(self):
        return self.enabled.get()

    def sensorDetected(self, rId):
        if self.isEnabled() and self.eventClass is not None:
            self.eventClass.sensorDetected(rId)

    def setSpeed(self, index, speed, useSmoothStart):
        self.speeds[index].set(speed)

        self.motors[index].setSpeed(speed, useSmoothStart)

    def getSpeed(self, index):
        return self.speeds[index].get();
