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
from sbrick import SBrick
from pfxbrick import PFxBrick
from functools import partial
import thread
from time import sleep

class Port:

    blebrick = 0
    channel = 0
    inverted = False

    def __init__(self, blebrick, channel, inverted):
        self.blebrick = blebrick
        self.channel = channel
        self.inverted = inverted

        blebrick.enableChannel(channel, False)

    def toggle(self, direction):
        self.blebrick.quickDrive(self.channel, direction if not self.inverted else not direction, 127, 0.4)

    def setSpeed(self, speed):
        self.blebrick.setSpeed(self.channel, speed)
        self.blebrick.setDuration(self.channel, 0.4)

    def setDirection(self, direction):
        if self.inverted:
            self.blebrick.setDirection(self.channel, not direction)
        else:
            self.blebrick.setDirection(self.channel, direction)

    def stop(self):
        self.blebrick.stop(self.channel)

class SwitchGroup:

    enabled = 0
    direction = True
    speed = 0
    blebrick = 0

    def __init__(self, xmlTag, ttkRoot, col, row):

        self.name = xmlTag.attrib['name']

        self.parseConfig(xmlTag)

        container = ttk.LabelFrame(ttkRoot)
        container.grid(row=row,column=col, sticky='wens', padx=5, pady=5)

        row1 = ttk.Frame(container)
        row1.pack(fill="x", padx=5);

        self.enabled = ttk.BooleanVar()
        enableChk = ttk.Checkbutton(row1, variable=self.enabled, command=self.onEnable);
        enableChk.pack(side=ttk.LEFT);

        self.statusLbl = ttk.Label(row1, text="disabled")
        self.statusLbl.pack(side=ttk.RIGHT);

        name = ttk.Label(row1, text=self.name)
        name.pack();

        self.imageSwitch = {'left': {False: None, True: None}, 'right': {False: None, True: None}}
        self.imageSwitch['left'][False] = ttk.PhotoImage(file="images/switch-left-off.gif")
        self.imageSwitch['left'][True] = ttk.PhotoImage(file="images/switch-left-on.gif")
        self.imageSwitch['right'][False] = ttk.PhotoImage(file="images/switch-right-off.gif")
        self.imageSwitch['right'][True] = ttk.PhotoImage(file="images/switch-right-on.gif")

        self.switchButtons = []
        for switch in self.switches:
            row2 = ttk.Frame(container)
            row2.pack(fill="x", pady=5, padx=5);

            switch_name = ttk.Label(row2, text=switch['name'])
            switch_name.pack(side=ttk.LEFT);
            
            switchBtn = ttk.Button(row2, image=self.imageSwitch[switch['direction']][False], state=ttk.DISABLED, relief=ttk.RAISED, command=partial(self.onToggleSwitch, len(self.switchButtons)))
            switchBtn.pack(side=ttk.RIGHT)
            self.switchButtons.append(switchBtn)

    def parseConfig(self, xmlTag):
        self.switches = []

        for child in xmlTag:
            if child.tag == 'sbrick':
                address = child.attrib['address']

                if self.blebrick is not 0:
                    raise Error('Only one BLEBrick is supported per switch group')
                
                sbrick = SBrick('hci0', address, self)
                self.blebrick = sbrick

                for channel in child:
                    if channel.tag == 'channel':
                        cId = channel.attrib['id']
                        service = channel.attrib['service']

                        if service == 'switch':
                            inverted = 'false'
                            if 'inverted' in channel.attrib:
                                inverted = channel.attrib['inverted']
                            self.switches.append({'port': Port(sbrick, int(cId), inverted == 'true'), 'direction': channel.attrib['direction'], 'name': channel.attrib['name'], 'on': False })
            elif child.tag == 'pfxbrick':
                address = child.attrib['address']
                
                if self.blebrick is not 0:
                    raise Error('Only one BLEBrick is supported per switch group')

                pfxbrick = PFxBrick('hci0', address, self)
                self.blebrick = pfxbrick

                for channel in child:
                    if channel.tag == 'channel':
                        cId = channel.attrib['id']
                        service = channel.attrib['service']

                        if service == 'switch':
                            inverted = 'false'
                            if 'inverted' in channel.attrib:
                                inverted = channel.attrib['inverted']
                            self.switches.append({'port': Port(pfxbrick, int(cId), inverted == 'true'), 'direction': channel.attrib['direction'], 'name': channel.attrib['name'], 'on': False })

    def stop(self):
        self.blebrick.disconnect()

    def getName(self):
        return self.name

    def getSwitches(self):
        switchNames = []
        for switch in self.switches:
            switchNames.append(switch['name'])
        return switchNames

    def getDirection(self, index):
        return self.switches[index]['direction']

    def onEnable(self):
       
        if self.enabled.get():
            self.blebrick.connect()
            self.statusLbl.config(text="connecting...", fg="black");
            i = 0
            for switchButton in self.switchButtons:
                switchButton.config(state=ttk.NORMAL)
                self.switchButtons[i].config(image=self.imageSwitch[self.switches[i]['direction']][False])
                self.switches[i]['port'].setDirection(False)
                self.switches[i]['on'] = False
                i = i + 1
        else:
            self.blebrick.disconnect()
            self.statusLbl.config(text="disabled", fg="black")
            i = 0
            for switchButton in self.switchButtons:
                switchButton.config(state=ttk.DISABLED, relief=ttk.RAISED)

                
    def onToggleSwitch(self, index):

        if self.switches[index]['on']:
            self.switchButtons[index].config(image=self.imageSwitch[self.switches[index]['direction']][False])
            self.switches[index]['port'].setDirection(False)
            self.switches[index]['on'] = False
        else:
            self.switchButtons[index].config(image=self.imageSwitch[self.switches[index]['direction']][True])
            self.switches[index]['port'].setDirection(True)
            self.switches[index]['on'] = True

        self.switches[index]['port'].toggle(self.switches[index]['on'])

        #thread.start_new_thread(self.stopSwitchMotor, (index,));

    #def stopSwitchMotor(self, *args):
    #    print(args)
    #    sleep(1)
    #    self.switches[args[0]].setSpeed(0)

    def setSwitch(self, index, on):
        if self.switches[index]['on'] != on:
            self.onToggleSwitch(index)

    def onBLEBrickError(self, fatal):
        if self.enabled.get():
            self.statusLbl.config(text="Error", fg="red");
            if not fatal:
                self.blebrick.connect()

    def onBLEBrickConnected(self):
        self.statusLbl.config(text="connected", fg="black");
        for switch in self.switches:
            switch['port'].toggle(switch['on'])

    def onBLEBrickSensorRead(self, val):
        self.statusLbl.config(text=val, fg="black");
        

