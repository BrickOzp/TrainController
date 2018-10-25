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
from sbrick import SBrick
from train import Train
from switchgroup import SwitchGroup
from devicegroup import DeviceGroup
from gpiohandler import GPIOHandler
from scenario import Scenario
import xml.etree.ElementTree as etree
import pexpect
import RPi.GPIO as GPIO
import datetime

class SensorDebugger(object):

    def __init__(self, root, trainControl):

        self.trainControl = trainControl
        self.top = ttk.Toplevel(root)

        self.top.geometry("300x500+300+300")

        frm = ttk.Frame(self.top, borderwidth=4, relief='ridge')
        frm.pack(fill='both', expand=True)

        self.text = ttk.Text(frm)
        self.text.pack(fill='both', expand=True)
        #self.text.config(state=ttk.DISABLED)

        self.top.protocol("WM_DELETE_WINDOW", self.onCloseSensorDebugger)

    def onCloseSensorDebugger(self):
        trainControl.stopSensorDebugger()
        self.top.destroy()

    def sensorDetected(self, rId):

        #self.text.config(state=ttk.NORMAL)
        self.text.insert('1.0', "[{}] {}\n".format(datetime.datetime.now().strftime('%H:%M:%S:%f'), rId))
        #self.text.config(state=ttk.DISABLED)

class TrainControl:

    def parseConfig(self, ttkRoot):
        self.sensorDebugger = None
        self.scenario = None
        
        configRoot = etree.parse('traincontrol.xml').getroot()
        col = 0
        row = 0
        container = ttk.Frame(ttkRoot)
        container.pack(fill="x")
        for child in configRoot:
            #if i % 2 == 0:
                #row = 
                #row.pack(fill="x");
            if child.tag == 'train':
                self.devices.append(Train(child, container, col, row, self))
            elif child.tag == 'switchgroup':
                self.devices.append(SwitchGroup(child, container, col, row))
            elif child.tag == 'devicegroup':
                self.devices.append(DeviceGroup(child, container, col, row))
            elif child.tag == 'gpio':
                self.devices.append(GPIOHandler(child, self))
            col = (col + 1) % 2
            if col == 0:
                row = row + 1

    def start(self, ttkRoot):
        self.devices = []
        self.parseConfig(ttkRoot)
        self.panicBtn = ttk.Button(ttkRoot, text="PANIC", bg="red", activebackground="red", command=self.onPanic, font=("Courier", 20))
        self.panicBtn.pack(padx=5, pady=5)

    def stop(self):
        #for device in self.devices:
            #if isinstance(device, GPIOHandler):
                #device.destroy()
        pass

    def getTrains(self):
        trains = []
        for device in self.devices:
            if isinstance(device, Train):
                trains.append(device)
        return trains

    def getSwitchGroups(self):
        switchgroups = []
        for device in self.devices:
            if isinstance(device, SwitchGroup):
                switchgroups.append(device)
        return switchgroups

    def getSensors(self):
        for device in self.devices:
            if isinstance(device, GPIOHandler):
                return device.getSensors()
        return []

    def sensorDetected(self, rId):
        for train in self.getTrains():
            train.sensorDetected(rId)

        if self.scenario is not None:
            self.scenario.sensorDetected(rId)

        if self.sensorDebugger is not None:
            self.sensorDebugger.sensorDetected(rId)

    def onPanic(self):
        for train in self.getTrains():
            train.onUpdateStop()

    def stopSensorDebugger(self):
        self.sensorDebugger = None

    def closeScenarioWindow(self):
        self.scenarioWindow = None

    def startScenario(self, scenario):
        self.scenario = scenario

    def stopScenario(self):
        self.scenario.stopScenario()
        self.scenario = None
        
        

def onClosing():
    trainControl.stop()
    root.destroy()

def debug_sensors():
    trainControl.sensorDebugger = SensorDebugger(root, trainControl)

def scenario():
    trainControl.scenarioWindow = Scenario(root, trainControl)

root = ttk.Tk()
    
root.title("Train controller")
root.geometry("635x500+300+300")

menubar = ttk.Menu(root)

filemenu = ttk.Menu(menubar, tearoff=0)
filemenu.add_command(label="Sensor debug", command=debug_sensors)
filemenu.add_command(label="Scenario", command=scenario)
menubar.add_cascade(label="File", menu=filemenu)

root.config(menu=menubar)

trainControl = TrainControl()
trainControl.start(root)

root.protocol("WM_DELETE_WINDOW", onClosing)
root.mainloop()

GPIO.cleanup()

print("Stopped");
