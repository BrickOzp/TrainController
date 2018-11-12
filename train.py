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
import time
from time import sleep
import sys
from event.stopandwait import StopAndWaitEvent
from event.twotrains import TwoTrainsEvent

class Port:

    blebrick = 0
    channel = 0
    inverted = False

    def __init__(self, blebrick, channel, inverted, useSmoothStart):
        self.blebrick = blebrick
        self.channel = channel
        self.inverted = inverted

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

class TrainPicker(object):

    root = None

    def __init__(self, train):

        self.train = train
        self.top = ttk.Toplevel(TrainPicker.root)

        frm = ttk.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        self.listbox = ttk.Listbox(frm)
        self.listbox.pack()

        self.trains = train.trainController.getTrains()
        self.trains.remove(train)

        connectedTo = self.train.getConnectedTo()

        self.listbox.insert(ttk.END, "Not connected")

        if connectedTo is None:
            self.listbox.selection_set(0)

        self.trains = [x for x in self.trains if x.isEnabled()]

        i = 1
        for atrain in self.trains:
            self.listbox.insert(ttk.END, atrain.getName())

            if connectedTo == atrain:
                self.listbox.selection_set(i)

            i = 1 + 1

        row = ttk.Frame(frm)
        row.pack(pady=5, padx=5);

        b_ok = ttk.Button(row, text='OK', command=self.onOkClick)
        b_ok.pack(side=ttk.LEFT)

        b_cancel = ttk.Button(row, text='Cancel')
        b_cancel['command'] = self.top.destroy
        b_cancel.pack(side=ttk.RIGHT)

    def onOkClick(self):
        selected = self.listbox.curselection()[0]
        if selected == 0:
            self.train.disconnectFromTrain()
        else:
            self.train.connectToTrain(self.trains[selected - 1])

        self.top.destroy()

class Train:

    enabled = 0
    direction = True
    speed = 0

    def __init__(self, xmlTag, ttkRoot, col, row, trainController):
        sys.path.append('./event')
        
        self.name = xmlTag.attrib['name']

        self.trainController = trainController
        self.connectedTo = None
        self.connectedTrains = []
        self.eventClass = None
        self.blebricks = []

        self.parseConfig(xmlTag)

        container = ttk.LabelFrame(ttkRoot)
        container.grid(row=row,column=col, sticky='n', padx=5, pady=5)

        row1 = ttk.Frame(container)
        row1.pack(fill="x", padx=5);

        self.enabled = ttk.BooleanVar()
        enableChk = ttk.Checkbutton(row1, variable=self.enabled, command=self.onEnable);
        enableChk.pack(side=ttk.LEFT);

        self.statusLbl = ttk.Label(row1, text="disabled")
        self.statusLbl.pack(side=ttk.RIGHT)

        self.timerLbl = ttk.Label(row1)
        self.timerLbl.pack(side=ttk.RIGHT)
        
        name = ttk.Label(row1, text=self.name)
        name.pack();

        row2 = ttk.Frame(container)
        row2.pack(fill="x", pady=5, padx=5);

        self.directionBtn = ttk.Button(row2, text=">", state=ttk.DISABLED, command=self.onDirectionToggled)
        self.directionBtn.pack(side=ttk.LEFT)

        self.speed = ttk.IntVar()
        self.speedScale = ttk.Scale(row2, from_=0, to=self.blebricks[0].getMaxSpeed(), length=250,
           orient=ttk.HORIZONTAL, variable=self.speed, state=ttk.DISABLED, command=self.onSpeedChanged)
        self.speedScale.pack(side=ttk.LEFT)

        row3 = ttk.Frame(container)
        row3.pack(fill="x", padx=5);

        self.stopBtn = ttk.Button(row3, text="STOP", bg="red", activebackground="red",
            state=ttk.DISABLED, command=self.onStop)
        self.stopBtn.pack(side=ttk.RIGHT, padx=5, pady=5)

        self.lightButtons = []
        self.lightOn = []
        for light in self.lights:
            lightBtn = ttk.Button(row3, text="L", state=ttk.DISABLED, relief=ttk.RAISED, command=partial(self.onToggleLight, len(self.lightButtons)))
            lightBtn.pack(side=ttk.LEFT)
            self.lightButtons.append(lightBtn)
            self.lightOn.append(False)

        self.connectBtn = ttk.Button(row3, text="C", state=ttk.DISABLED, command=self.onConnectTrain)
        self.connectBtn.pack(side=ttk.LEFT) 

        self.eventVar = ttk.StringVar(ttkRoot)
        self.eventVar.set('None')
        self.eventVar.trace('w', partial(self.onEventChanged, self.eventVar))
        eventTypes = ['None', 'StopAndWait', 'TwoTrains']
        if self.event_class_name is not None:
            eventTypes.append('Custom')

        self.eventOM = apply(ttk.OptionMenu, (row3, self.eventVar) + tuple(eventTypes))
        self.eventOM.config(state='disabled')
        self.eventOM.pack(side=ttk.LEFT)

        self.settingsImage = ttk.PhotoImage(file="images/settings.png")
        self.eventSettingsBtn = ttk.Button(row3, image=self.settingsImage, state=ttk.DISABLED, command=self.onEventSettings)
        self.eventSettingsBtn.pack(side=ttk.LEFT)

        TrainPicker.root = ttkRoot
        self.ttkRoot = ttkRoot

    def parseConfig(self, xmlTag):
        self.motors = []
        self.lights = []
        self.event_class_name = None

        for child in xmlTag:
            if child.tag == 'sbrick':
                address = child.attrib['address']
                
                sbrick = SBrick('hci0', address, self)
                self.blebricks.append(sbrick)

                for channel in child:
                    if channel.tag == 'channel':
                        cId = channel.attrib['id']
                        service = channel.attrib['service']

                        if service == 'motor':
                            inverted = 'false'
                            if 'inverted' in channel.attrib:
                                inverted = channel.attrib['inverted']
                            self.motors.append(Port(sbrick, int(cId), inverted == 'true', True))
                        elif service == 'light':
                            self.lights.append(Port(sbrick, int(cId), False, False))
            elif child.tag == 'pfxbrick':
                address = child.attrib['address']

                pfxbrick = PFxBrick('hci0', address, self)
                self.blebricks.append(pfxbrick)

                for channel in child:
                    if channel.tag == 'channel':
                        cId = channel.attrib['id']
                        service = channel.attrib['service']

                        if service == 'motor':
                            inverted = 'false'
                            if 'inverted' in channel.attrib:
                                inverted = channel.attrib['inverted']
                            self.motors.append(Port(pfxbrick, int(cId), inverted == 'true', True))
            elif child.tag ==  'event':
                self.event_class_name = child.attrib['class_name']

    #def stop(self):
    #    self.sbrick.disconnect()

    def onEnable(self):
       
        if self.enabled.get():
            for blebrick in self.blebricks:
                blebrick.connect()
            self.statusLbl.config(text="connecting...", fg="black");
            self.directionBtn.config(state='normal')
            self.speedScale.config(state='normal')
            self.stopBtn.config(state='normal')
            for lightButton in self.lightButtons:
                lightButton.config(state=ttk.NORMAL)
            self.connectBtn.config(state='normal')
            self.eventOM.config(state='normal')
        else:
            if self.speed.get() > 0:
                for blebrick in self.blebricks:
                    blebrick.stop()
                sleep(0.3)
            self.disconnectFromTrain()
            for blebrick in self.blebricks:
                blebrick.disconnect()
            self.directionBtn.config(state='disabled')
            self.speedScale.config(state='disabled')
            self.speed.set(0)
            self.stopBtn.config(state='disabled')
            self.statusLbl.config(text="disabled", fg="black")
            self.timerLbl.config(text="")
            self.enableTimerUpdate = False
            i = 0
            for lightButton in self.lightButtons:
                lightButton.config(state=ttk.DISABLED, relief=ttk.RAISED)
                self.lightOn[i] = False
                i = i + 1
            self.connectBtn.config(state='disabled')
            self.eventOM.config(state=ttk.DISABLED)
            self.eventVar.set('None')

    def onStop(self):
        self.speed.set(0)
        self.directionBtn.config(state='normal')

        for motor in self.motors:
            motor.setSpeed(0)

        for motor in self.motors:
            motor.stop()

        for connectedTrain in self.connectedTrains:
            connectedTrain.onUpdateStop()
            
    def onSpeedChanged(self, val):
        if not self.enabled.get() or self.speed.get() > 0:
            self.directionBtn.config(state='disabled')
        else:
            self.directionBtn.config(state='normal')

        for motor in self.motors:
            motor.setSpeed(self.speed.get())

        for connectedTrain in self.connectedTrains:
            connectedTrain.onUpdateSpeed(self.speed.get())

    def onDirectionToggled(self):
        self.direction = not self.direction

        if self.direction:
            self.directionBtn.config(text='>')
        else:
            self.directionBtn.config(text='<')

        for motor in self.motors:
            motor.setDirection(self.direction)

        for connectedTrain in self.connectedTrains:
            connectedTrain.toggleDirection()

        if  self.eventClass is not None:
            self.eventClass.directionToggled(self.direction)

    def onToggleLight(self, index):

        if self.lightOn[index]:
            self.lightButtons[index].config(relief=ttk.RAISED)
            self.lights[index].setSpeed(0)
            self.lightOn[index] = False
        else:
            self.lightButtons[index].config(relief=ttk.SUNKEN)
            self.lights[index].setSpeed(255)
            self.lightOn[index] = True

    def onConnectTrain(self):        
        TrainPicker(self)        

    def onEventChanged(self, newEvent, *args):
        if newEvent.get() == "None":
            self.eventClass = None
            self.eventSettingsBtn.config(state='disabled')
        elif newEvent.get() == "StopAndWait":
            if not isinstance(self.eventClass, StopAndWaitEvent):
                self.eventClass = StopAndWaitEvent(self)
                self.eventSettingsBtn.config(state='normal')
        elif newEvent.get() == "TwoTrains":
            if not isinstance(self.eventClass, TwoTrainsEvent):
                self.eventClass = TwoTrainsEvent(self)
                self.eventSettingsBtn.config(state='normal')
        elif newEvent.get() == "Custom":
            clazz = locate(self.event_class_name, 1)
            if clazz is not None:
                self.eventClass = clazz(self)
            else:
                print("Could not find {}".format(self.event_class_name))
                self.eventVar.set('None')
            self.eventSettingsBtn.config(state='disabled')
        

    def onEventSettings(self):
        if self.eventClass is not None:
            self.eventClass.openSettings(self.ttkRoot)

    def onBLEBrickError(self, fatal):
        if self.enabled.get():
            self.statusLbl.config(text="Error", fg="red");
            self.enableTimerUpdate = False
            for motor in self.motors:
                motor.stop()
            if not fatal:
                for blebrick in self.blebricks:
                    #if not blebrick.isConnected()
                    blebrick.connect()

    def onBLEBrickConnected(self):
        for blebrick in self.blebricks:
            if not blebrick.isConnected():
                return
        self.statusLbl.config(text="connected", fg="black")
        self.connectionTime = time.time()
        self.enableTimerUpdate = True
        self.updateTimer()
        for motor in self.motors:
            motor.setDirection(self.direction)
            motor.setSpeed(self.speed.get())

    def onBLEBrickSensorRead(self, val):
        self.statusLbl.config(text=val, fg="black");

    def updateTimer(self):
        if self.enableTimerUpdate:
            duration = time.time() - self.connectionTime
        # get the current local time from the PC
        # if time string has changed, update it
            self.timerLbl.config(text=time.strftime("%H:%M:%S", time.gmtime(duration)))
        #.strftime('%H:%M:%S')
        # calls itself every 200 milliseconds
        # to update the time display as needed
        # could use >200 ms, but display gets jerky
        
            self.timerLbl.after(200, self.updateTimer)

    def getName(self):
        return self.name

    def isEnabled(self):
        return self.enabled.get()

    def disconnectFromTrain(self):
        if self.connectedTo is not None:
            self.connectedTo.disconnect(self)
            self.speedScale.config(state='normal')
            self.connectedTo = None

    def connectToTrain(self, other_train):
        self.disconnectFromTrain()

        self.connectedTo = other_train.connect(self)

        self.speedScale.config(state='disabled')

    def disconnect(self, other_train):
        self.connectedTrains.remove(other_train)

        if len(self.connectedTrains) == 0:
            self.connectBtn.config(state='normal')

    def connect(self, other_train):

        self.connectBtn.config(state='disabled')
        self.connectedTrains.append(other_train)
        
        return self

    def getConnectedTo(self):
        return self.connectedTo

    def onUpdateSpeed(self, speed):
        self.speed.set(speed)
        
        if not self.enabled.get() or self.speed.get() > 0:
            self.directionBtn.config(state='disabled')
        else:
            self.directionBtn.config(state='normal')

        for motor in self.motors:
            motor.setSpeed(speed)

    def onUpdateStop(self):
        if self.isEnabled():
            self.speed.set(0)
            self.directionBtn.config(state='normal')

            for motor in self.motors:
                motor.setSpeed(0)

            for motor in self.motors:
                motor.stop()

    def sensorDetected(self, rId):
        if self.isEnabled() and self.eventClass is not None:
            self.eventClass.sensorDetected(rId)

    def setSpeed(self, speed, useSmoothStart):
        self.speed.set(speed)

        if not self.enabled.get() or self.speed.get() > 0:
            self.directionBtn.config(state='disabled')
        else:
            self.directionBtn.config(state='normal')

        for motor in self.motors:
            motor.setSpeed(speed, useSmoothStart)

        for connectedTrain in self.connectedTrains:
            connectedTrain.onUpdateSpeed(self.speed.get())

    def getSpeed(self):
        return self.speed.get();

    def toggleDirection(self):
        self.direction = not self.direction

        if self.direction:
            self.directionBtn.config(text='>')
        else:
            self.directionBtn.config(text='<')

        for motor in self.motors:
            motor.setDirection(self.direction)

        if  self.eventClass is not None:
            self.eventClass.directionToggled(self.direction)

    def setLight(self, index, on):

        if on:
            self.lightButtons[index].config(relief=ttk.SUNKEN)
            self.lights[index].setSpeed(255)
            self.lightOn[index] = True
        else:
            self.lightButtons[index].config(relief=ttk.RAISED)
            self.lights[index].setSpeed(0)
            self.lightOn[index] = False

    def getTrainController(self):
        return self.trainController
