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

from threading import Lock, RLock
from bluepy.btle import Peripheral, DefaultDelegate, BTLEException

class BluetoothLEError(Exception):
    def __repr__(self):
        return '<%s, %s>' % (self.__class__.__name__, self.message)

class NotConnectedError(BluetoothLEError):
    pass

class NoResponseError(BluetoothLEError):
    pass


class BTLEDevice(object):
    def __init__(self, mac_address, hci_device='hci0'):
        self._address = mac_address
        self._lock = Lock()
        self._connection_lock = RLock()
        self._connected = False
        self._peripheral = Peripheral()

    def read(self, handle):
        with self._connection_lock:
            if not self._connected:
                message = 'device is not connected'
                raise NotConnectedError(message)
        
            try:
                return self._peripheral.readCharacteristic(handle)
            except BTLEException as e:
                raise(NotConnectedError())

    def write(self, handle, value, wait_for_response=False):
        with self._connection_lock:
            if not self._connected:
                message = 'device is not connected'
                raise NotConnectedError(message)
        
            try:
                self._peripheral.writeCharacteristic(handle, bytearray.fromhex(value), wait_for_response)
            except BTLEException:
                raise NoResponseError()

    def connect(self):
        try:
            self._peripheral.connect(self._address)
            self._connected = True
        except BTLEException:
            message = "Could not connect to {}".format(self._address)
            raise NotConnectedError(message)

    def stop(self):
        if self._connected:
            self._peripheral.withDelegate(None)
            try:
                self._peripheral.disconnect()
            except BTLEException:
                pass
            self._connected = False

    def subscribe(self, handle, callback=None, _type=0):
        if _type not in {0, 1, 2}:
            message = ('Type must be 0 (notifications), 1 (indications), or'
                       '2 (both).')
            raise ValueError(message)

        control_handle = handle + 1
        write = "0100" if _type == 0 else \
                "0200" if _type == 1 else \
                "0300"

        self._peripheral.withDelegate(NotificationDelegate(callback))

        with self._lock:
            self.write(control_handle, write, wait_for_response=True)

    def unsubscribe(self, handle):
        control_handle = handle + 1
        value = bytearray([0,0])
        with self._lock:
            self.write(control_handle, value, wait_for_response=True)


class NotificationDelegate(DefaultDelegate):
    def __init__(self, callback):
        self._cb = callback
    
    def handleNotification(self, cHandle, data):
        self._cb(cHandle, bytearray(data))
