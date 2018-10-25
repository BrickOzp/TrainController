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
import Tkinter as ttk

class TwoTrainsEvent:

    def __init__(self, train):
        print("TwoTrainsEvent init");
        self.train = train

        self.sensorStop = ''
        self.sensorStart = ''
        self.delay = 1.0

        self.speed = train.getSpeed()
        self.expectingStop = True

    def sensorDetected(self, rId):
        if rId == self.sensorStop:
            if self.expectingStop:
                thread.start_new_thread(self.stop, ());
                self.expectingStop = False
            else:
                self.expectingStop = True
        elif rId == self.sensorStart:
            if not self.expectingStop:
                self.train.setSpeed(self.speed, True)

    def stop(self, *args):
        self.speed = self.train.getSpeed()

        sleep(self.delay)

        self.train.onStop()

    def directionToggled(self, direction):
        pass

    def openSettings(self, ttkRoot):
        self.top = ttk.Toplevel(ttkRoot)

        frm = ttk.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        row = ttk.Frame(frm)
        row.pack(pady=5, padx=5)

        sensors = self.train.getTrainController().getSensors()

        ttk.Label(row, text="Stop sensor:").pack(side=ttk.LEFT)

        self.sensorStopVar = ttk.StringVar(ttkRoot)
        self.sensorStopVar.set(self.sensorStop if self.sensorStop is not '' else sensors[0])

        self.sensorStopOM = apply(ttk.OptionMenu, (row, self.sensorStopVar) + tuple(sensors))
        self.sensorStopOM.pack(side=ttk.RIGHT)

        row2 = ttk.Frame(frm)
        row2.pack(pady=5, padx=5)

        ttk.Label(row2, text="Delay time (sec):").pack(side=ttk.LEFT)

        self.delayText = ttk.Text(row2, height=1, width=5)
        self.delayText.pack(side=ttk.RIGHT)
        self.delayText.insert(ttk.END, str(self.delay))

        row3 = ttk.Frame(frm)
        row3.pack(pady=5, padx=5)

        ttk.Label(row3, text="Start sensor:").pack(side=ttk.LEFT)

        self.sensorStartVar = ttk.StringVar(ttkRoot)
        self.sensorStartVar.set(self.sensorStart if self.sensorStart is not '' else sensors[0])

        self.sensorStartOM = apply(ttk.OptionMenu, (row3, self.sensorStartVar) + tuple(sensors))
        self.sensorStartOM.pack(side=ttk.RIGHT)

        row4 = ttk.Frame(frm)
        row4.pack(pady=5, padx=5)

        b_ok = ttk.Button(row4, text='OK', command=self.onOkClick)
        b_ok.pack(side=ttk.LEFT)

        b_cancel = ttk.Button(row4, text='Cancel')
        b_cancel['command'] = self.top.destroy
        b_cancel.pack(side=ttk.RIGHT)

    def onOkClick(self):
        self.sensorStop = self.sensorStopVar.get()
        self.sensorStart = self.sensorStartVar.get()
        self.delay = float(self.delayText.get("1.0",'end-1c'))
        print("TwoTrains sensorStop: {} delay: {} sensorStart: {}".format(self.sensorStop, self.delay, self.sensorStart))
        self.top.destroy()
