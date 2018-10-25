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

import Tkinter as ttk
from functools import partial
from pydoc import locate
import sys

class Scenario(object):

    def __init__(self, root, trainControl):
        sys.path.append('./scenarios')

        self.started = False
        self.trains = trainControl.getTrains()
        self.switchgroups = trainControl.getSwitchGroups()
        self.sensors = trainControl.getSensors()
        self.trainnames = ['']
        for train in self.trains:
            self.trainnames.append(train.getName())
        switchgroupnames = []
        for sg in self.switchgroups:
            switchgroupnames.append(sg.getName())

        self.trainControl = trainControl
        self.top = ttk.Toplevel(root)

        self.top.geometry("340x500+300+300")

        self.imageSwitch = {}
        self.imageSwitch['left'] = ttk.PhotoImage(file="images/switch-left-off.gif")
        self.imageSwitch['right'] = ttk.PhotoImage(file="images/switch-right-off.gif")

        row1 = ttk.Frame(self.top)
        row1.pack(fill='x', padx=15)

        train1Lbl = ttk.Label(row1, text="Train 1")
        train1Lbl.pack(side=ttk.LEFT)

        train1Lbl = ttk.Label(row1, text="Train 2")
        train1Lbl.pack(side=ttk.RIGHT)

        row2 = ttk.Frame(self.top)
        row2.pack(fill='x', padx=15)

        self.train = []
        self.train.append(ttk.StringVar(root))
        self.train[0].set(self.trainnames[0]) # default value
        
        w = apply(ttk.OptionMenu, (row2, self.train[0]) + tuple(self.trainnames))
        w.pack(side=ttk.LEFT)

        self.train.append(ttk.StringVar(root))
        self.train[1].set(self.trainnames[0]) # default value

        w = apply(ttk.OptionMenu, (row2, self.train[1]) + tuple(self.trainnames))
        w.pack(side=ttk.RIGHT)

        row3 = ttk.Frame(self.top)
        row3.pack(fill='x', padx=15)

        self.sensor = []
        self.sensor.append(ttk.StringVar(root))
        self.sensor[0].set(self.sensors[0]) # default value
        
        w = apply(ttk.OptionMenu, (row3, self.sensor[0]) + tuple(self.sensors))
        w.pack(side=ttk.LEFT)

        self.sensor.append(ttk.StringVar(root))
        self.sensor[1].set(self.sensors[0]) # default value

        w = apply(ttk.OptionMenu, (row3, self.sensor[1]) + tuple(self.sensors))
        w.pack(side=ttk.RIGHT)

        row4 = ttk.Frame(self.top)
        row4.pack(fill='x', padx=15)

        self.switchBtn = []
        self.switchBtn.append(ttk.Button(row4))

        self.switches = []
        self.switches.append(ttk.StringVar(root))
        self.switches[0].set('') # default value
        self.switches[0].trace('w', partial(self.switchChanged, 0, self.switches[0]))

        self.switchOM = []
        self.switchOM.append(ttk.OptionMenu(row4, self.switches[0], ''))

        self.switchgroup = []
        self.switchgroup.append(ttk.StringVar(root))
        self.switchgroup[0].trace('w', partial(self.switchGroupChanged, 0, self.switchgroup[0]))
        self.switchgroup[0].set(switchgroupnames[0]) # default value

        self.switchgroupOM = []
        self.switchgroupOM.append(apply(ttk.OptionMenu, (row4, self.switchgroup[0]) + tuple(switchgroupnames)))
        self.switchgroupOM[0].pack(side=ttk.LEFT)

        self.switchOM[0].pack(side=ttk.RIGHT)

        self.switchBtn[0].pack()

        emptyrow = ttk.Frame(self.top)
        emptyrow.pack(fill='x', pady=15)
        
        row7 = ttk.Frame(self.top)
        row7.pack(fill='x', padx=15)

        train1Lbl = ttk.Label(row7, text="Train 3")
        train1Lbl.pack(side=ttk.LEFT)

        train1Lbl = ttk.Label(row7, text="Train 4")
        train1Lbl.pack(side=ttk.RIGHT)

        row8 = ttk.Frame(self.top)
        row8.pack(fill='x', padx=15)

        self.train.append(ttk.StringVar(root))
        self.train[2].set(self.trainnames[0]) # default value
        
        w = apply(ttk.OptionMenu, (row8, self.train[2]) + tuple(self.trainnames))
        w.pack(side=ttk.LEFT)

        self.train.append(ttk.StringVar(root))
        self.train[3].set(self.trainnames[0]) # default value

        w = apply(ttk.OptionMenu, (row8, self.train[3]) + tuple(self.trainnames))
        w.pack(side=ttk.RIGHT)

        row6 = ttk.Frame(self.top)
        row6.pack(fill='x', padx=15)

        self.sensor.append(ttk.StringVar(root))
        self.sensor[2].set(self.sensors[0]) # default value
        
        w = apply(ttk.OptionMenu, (row6, self.sensor[2]) + tuple(self.sensors))
        w.pack(side=ttk.LEFT)

        self.sensor.append(ttk.StringVar(root))
        self.sensor[3].set(self.sensors[0]) # default value

        w = apply(ttk.OptionMenu, (row6, self.sensor[3]) + tuple(self.sensors))
        w.pack(side=ttk.RIGHT)

        row5 = ttk.Frame(self.top)
        row5.pack(fill='x', padx=15)

        self.switchBtn.append(ttk.Button(row5))

        self.switches.append(ttk.StringVar(root))
        self.switches[1].set('') # default value
        self.switches[1].trace('w', partial(self.switchChanged, 1, self.switches[1]))

        self.switchOM.append(ttk.OptionMenu(row5, self.switches[1], ''))

        self.switchgroup.append(ttk.StringVar(root))
        self.switchgroup[1].trace('w', partial(self.switchGroupChanged, 1, self.switchgroup[1]))
        self.switchgroup[1].set(switchgroupnames[0]) # default value
        
        self.switchgroupOM.append(apply(ttk.OptionMenu, (row5, self.switchgroup[1]) + tuple(switchgroupnames)))
        self.switchgroupOM[1].pack(side=ttk.LEFT)

        self.switchOM[1].pack(side=ttk.RIGHT)

        self.switchBtn[1].pack()

        row9 = ttk.Frame(self.top)
        row9.pack(fill='x', padx=15)

        self.startBtn = ttk.Button(row9, text="Start", command=self.onToggleScenario)
        self.startBtn.pack()

        #self.text = ttk.Text(frm)
        #self.text.pack(fill='both', expand=True)
        #self.text.config(state=ttk.DISABLED)

        self.top.protocol("WM_DELETE_WINDOW", self.onCloseScenario)

    def switchGroupChanged(self, index, var, *args):
        for i in range(len(self.switchgroups)):
            if self.switchgroups[i].getName() == var.get():
                switchNames = self.switchgroups[i].getSwitches()

                self.switches[index].set(switchNames[0])

                menu = self.switchOM[index]['menu']
                menu.delete(0, 'end')

                for switchName in switchNames:
                    menu.add_command(label=switchName, command=lambda nation=switchName: self.switches[index].set(nation))
                break

    def switchChanged(self, index, var, *args):
        for i in range(len(self.switchgroups)):
            if self.switchgroups[i].getName() == self.switchgroup[index].get():
                switchNames = self.switchgroups[i].getSwitches()
                for j in range(len(switchNames)):
                    if switchNames[j] == var.get():
                        self.switchBtn[index].config(image=self.imageSwitch[self.switchgroups[i].getDirection(j)])

    def onToggleScenario(self):
        if not self.started:

            trains = [None] * 4
            for i in range(4):
                if self.train[i].get() != '':
                    for j in range(len(self.trainnames) - 1):
                        if self.train[i].get() == self.trainnames[j]:
                            trains[i] = self.trains[j]
                        
            sensors = [None] * 4
            for i in range(4):
                sensors[i] = self.sensor[i].get()

            switchGroups = [None] * 2
            switchIndex = [None] * 2
            for i in range(2):
                for j in range(len(self.switchgroups)):
                    if self.switchgroups[j].getName() == self.switchgroup[i].get():
                        switchNames = self.switchgroups[j].getSwitches()
                        switchGroups[i] = self.switchgroups[j]
                        for k in range(len(switchNames)):
                            if switchNames[k] == self.switches[i].get():
                                switchIndex[i] = k

            clazz = locate("singletrack.SingeTrackScenario", 1)
            if clazz is not None: 
                self.trainControl.startScenario(clazz(trains, sensors, switchGroups, switchIndex))

                self.startBtn.config(text="Stop")
                self.started = True
            else:
                print("Could not find scenario")
        else:
            self.trainControl.stopScenario()
            self.startBtn.config(text="Start")
            self.started = False
        
    def onCloseScenario(self):
        self.trainControl.closeScenarioWindow()
        self.top.destroy()
