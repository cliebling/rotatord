#!/usr/bin/python 
"""
rotatord.py
Implements a rot2prog compliant antenna az/el rotator
on a Raspberry Pi

Copyright (C) 2020 Charles R. Liebling

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from __future__ import division
import serial
import getopt
import sys
import time
import RPi.GPIO as gpio
from Queue import Queue
from threading import Thread


# Define the rotator commands per rot2prog
CmdStop = 0x0F
CmdStatus = 0x1F
CmdSet = 0x2F
# There isn't an exit command in the rot2prog specification
# 0x3F isn't specified in te rot2prog command set, so just define it as the quit command
CmdQuit = 0x3F

ElStep = 3 
ElDirection = 5
ElEnable = 7
AzStep = 11
AzDirection = 13
AzEnable = 15

def waitForCommand(serialPort):
        command = ""
        byte = 'A'
        while byte != 'W':
                byte = serialPort.read()
        # Command detected
        print hex(ord(byte))
        command = command + byte
        while byte != ' ':
                byte = serialPort.read()
                print hex(ord(byte))
                command = command + byte
        # If we get a space, the command has terminated
        return command

def checkCommand(command):
        return len(command) == 13

def getCmdType(command):
        return ord(command[11])

def calcAzimuth(command):
        H1 = int(command[1])
        H2 = int(command[2])
        H3 = int(command[3])
        H4 = int(command[4])
        PH = ord(command[5])
        pulses = (H1 * 1000) + (H2 * 100) + (H3 * 10) + H4
        azimuth = (pulses / PH) - 360.0
        return azimuth

def calcElevation(command):
        V1 = int(command[6])
        V2 = int(command[7])
        V3 = int(command[8])
        V4 = int(command[9])
        PV = ord(command[10])
        pulses = (V1 * 1000) + (V2 * 100) + (V3 * 10) + V4
        elevation = (pulses / PV) - 360.0
        return elevation

def stepAzCW(steps):
        global AzStep
        global AzDirection
        global AzEnable
        print "Stepping azimuth clockwise: ", steps
        #gpio.output(AzEnable, True)
        gpio.output(AzDirection, False)
        time.sleep(0.001)
        for a in range(0, int(steps)):
                gpio.output(AzStep, True)
                time.sleep(0.001)
                gpio.output(AzStep, False)
                time.sleep(0.001)
        #gpio.output(AzEnable, False)

def stepAzCCW(steps):
        global AzStep
        global AzDirection
        global AzEnable
        print "Stepping azimuth counterclockwise: ", steps
        #gpio.output(AzEnable, True)
        gpio.output(AzDirection, True)
        time.sleep(0.001)
        for a in range(0, int(steps)):
                gpio.output(AzStep, True)
                time.sleep(0.001)
                gpio.output(AzStep, False)
                time.sleep(0.001)
        #gpio.output(AzEnable, False)

def stepElCW(steps):
        global ElStep
        global ElDirection
        global ElEnable
        print "Stepping elevation clockwise: ", steps
        #gpio.output(ElEnable, True)
        gpio.output(ElDirection, True)
        time.sleep(0.001)
        for a in range(0, int(steps)):
                gpio.output(ElStep, True)
                time.sleep(0.001)
                gpio.output(ElStep, False)
                time.sleep(0.001)
        #gpio.output(ElEnable, False)

def stepElCCW(steps):
        global ElStep
        global ElDirection
        global ElEnable
        print "Stepping elevation counterclockwise: ", steps
        #gpio.output(ElEnable, True)
        gpio.output(ElDirection, False)
        time.sleep(0.001)
        for a in range(0, int(steps)):
                gpio.output(ElStep, True)
                time.sleep(0.001)
                gpio.output(ElStep, False)
                time.sleep(0.001)
        #gpio.output(ElEnable, False)

def moveRotatorTo(azimuth, newAzimuth, elevation, newElevation, stepsPerDegree):
        azimuthDegrees = 0.0
        elevationDegrees = 0.0
        azimuthSteps = 0
        elevationSteps = 0
        azimuthDegrees = newAzimuth - azimuth
        elevationDegrees = newElevation - elevation
        azimuthSteps = abs(azimuthDegrees * stepsPerDegree) * 60
        elevationSteps = abs(elevationDegrees * stepsPerDegree) * 60
        if azimuthDegrees > 0.0:
                stepAzCW(azimuthSteps)
        elif azimuthDegrees < 0.0:
                stepAzCCW(azimuthSteps)
        else:
                pass
        if elevationDegrees > 0.0:
                stepElCW(elevationSteps)
        elif elevationDegrees < 0.0:
                stepElCCW(elevationSteps)
        else:
                pass

def sendStatus(serialPort, azimuth, elevation, PH, PV):
        # Add 360 to comply with rot2prog
        azimuth = azimuth + 360.0
        elevation = elevation + 360.0
        S = 'W'
        K = chr(0x1F)
        H1 = chr(int(azimuth // 100))
        azimuth = azimuth % 100
        H2 = chr(int(azimuth // 10))
        azimuth = azimuth % 10
        H3 = chr(int(azimuth // 1))
        azimuth = azimuth % 1
        H4 = chr(int(azimuth * 10))
        V1 = chr(int(elevation // 100))
        elevation = elevation % 100
        V2 = chr(int(elevation // 10))
        elevation = elevation % 10
        V3 = chr(int(elevation // 1))
        elevation = elevation % 1
        V4 = chr(int(elevation * 10))
        response = S + H1 + H2 + H3 + H4 + chr(int(PH)) + V1 + V2 + V3 +V4 + chr(int(PV)) + chr(0x20)
        serialPort.write(response)

def stopRotator():
        pass

def printUsage():
        print """-h: This help menu
                 -p: path to serial device
                 -s: steps per degree that hamlib expects
                 -b baud rate\n"""

def dequeueAndMove(moveQueue):
        global AzStep
        global AzDirection
        global AzEnable
        global ElStep
        global ElDirection
        global ElEnable
        
        gpio.setmode(gpio.BOARD)
        gpio.setup([ElStep, ElDirection, ElEnable], gpio.OUT)
        gpio.setup([AzStep, AzDirection, AzEnable], gpio.OUT)
        gpio.output(AzEnable, True)
        gpio.output(ElEnable, True)
        print "Move thread started"
        azimuthDegrees = 0.0
        elevationDegrees = 0.0
        azimuth = 0.0
        newAzimuth = 0.0
        elevation = 0.0
        newElevation = 0.0
        azimuthSteps = 0
        elevationSteps = 0
        while True:
                newAzimuth, newElevation, stepsPerDegree = moveQueue.get()
                # Handle the exit condition and bail
                if newAzimuth == 1 and newElevation == -1 and stepsPerDegree == -1:
                        break
                azimuthDegrees = newAzimuth - azimuth
                elevationDegrees = newElevation - elevation
                azimuthSteps = abs(azimuthDegrees * stepsPerDegree) * 60
                elevationSteps = abs(elevationDegrees * stepsPerDegree) * 60
                print "Moving azimuth", azimuthSteps, "steps"
                print "Moving elevation", elevationSteps, "steps"
                if azimuthDegrees > 0.0:
                        stepAzCW(azimuthSteps)
                elif azimuthDegrees < 0.0:
                        stepAzCCW(azimuthSteps)
                else:
                        pass
                if elevationDegrees > 0.0:
                        stepElCW(elevationSteps)
                elif elevationDegrees < 0.0:
                        stepElCCW(elevationSteps)
                else:
                        pass
                azimuth = newAzimuth
                elevation = newElevation
        return

def main():
        global CmdStop
        global CmdStatus
        global CmdSet
        moveQueue = Queue(maxsize=0)
        moveThread = Thread(target=dequeueAndMove, args=(moveQueue,))
        try:
                opts, args = getopt.getopt(sys.argv[1:], "p:s:b:h")
        except getopt.GetoptError as err:
                sys.exit(2)
        print "Going to parse options"
        # Some defaults
        serialDevice = "/dev/ttyS0"
        baudRate = 9600
        stepsPerDegree = 1.0
        azimuth = 0.0
        elevation = 0.0
        newAzimuth = 0.0
        newElevation = 0.0
        command = ""
        print opts
        for o, a in opts:
                if o == "-p":
                        serialDevice = a
                elif o == "-b":
                        baudRate = int(a)
                elif o == "-s":
                        stepsPerDegree = float(a)
                elif o == "-h":
                        printUsage()
                        sys.exit()
                else:
                        assert False, "Bad option given"
        if baudRate not in [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
                print "Bad baud rate specified!"
                sys.exit(2)
        PH = stepsPerDegree
        PV = stepsPerDegree
        moveThread.start()
        serialPort = serial.Serial(serialDevice, baudrate = baudRate)
        while True:        
                command = waitForCommand(serialPort)
                print "Got a command"
                print command
                if checkCommand(command) == False:
                        continue
                elif getCmdType(command) == CmdStop:
                        stopRotator()
                elif getCmdType(command) == CmdStatus:
                        sendStatus(serialPort, azimuth, elevation, PH, PV)
                elif getCmdType(command) == CmdSet:
                        print "Got a set command"
                        newAzimuth = calcAzimuth(command)
                        newElevation = calcElevation(command)
                        print "Setting Azimuth to ", newAzimuth
                        print "Setting Elevation to ", newElevation
                        # moveRotatorTo(azimuth, newAzimuth, elevation, newElevation, stepsPerDegree)
                        moveQueue.put([newAzimuth, newElevation, stepsPerDegree])
                        azimuth = newAzimuth
                        elevation = newElevation
                elif getCmdType(command) == CmdQuit:
                        # Use all negative 1s as a terminate condition
                        moveQueue.put([-1, -1, -1])
                        break
        return 0

if __name__ == "__main__":
        main()
