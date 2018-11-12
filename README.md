#Train Controller

This is an application designed for controlling LEGO trains, equipped with SBrick or PfxBrick, from a Raspberry pi.

## Requirements
* Python 2.7
* BlueZ
* bluepy

### BlueZ
BlueZ is the official Bluetooth stack on Linux.

### bluepy
bluepy is a Python module which provides an interface to Bluetooth LE on Linux.<br />
Ref: https://github.com/IanHarvey/bluepy
```bash
$ pip install bluepy
```

## Usage
```bash
$ python traincontrol.py
```

### How to find the bluetooth address
```bash
$ sudo hcitool lescan
```
