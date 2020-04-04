#!/bin/python 
from __future__ import division
import serial
import getopt
import sys

# Rot2Prog implementation (c) 2020 C. Liebling W3PZ crlieb@swbell.net
# Distributed under the GPLv2

def waitForCommand(serialPort)
        command = ""
        byte = 'A'
        while byte != 'W':
                byte = serialPort.read()
        # Command detected
        command = command + byte
        while byte != ' ':
                byte = serialPort.read()
                command = command + byte
        # If we get a space, the command has terminated
        return command

def checkCommand(command):
        return len(command) == 13

def calcAzimuth(command):
        H1 = int(command[1])
        H2 = int(command[2])
        H3 = int(command[3])
        H4 = int(command[4])
        PH = int(command[5])
        pulses = (H1 * 1000) + (H2 * 100) + (H3 * 10) + H4
        azimuth = (pulses / PH) - 360.0
        return azimuth

def calcElevation(command):
        V1 = int(command[6])
        V2 = int(command[7])
        V3 = int(command[8])
        V4 = int(command[9])
        PV = int(command[10])
        pulses = (V1 * 1000) * (V2 * 100) + (V3 * 10) + V4
        elevation = (pulses / PV) - 360.0
        return elevation

def stepAzCW(steps):
        pass

def stepAzCCW(steps):
        pass

def stepElCW(steps):
        pass

def stepElCCW(steps):
        pass

def main()
        try:
                opts, args = getopt.getopt(sys.argv[1:], "p:")
        except getopt.GetoptError as err:
                sys.exit(2)
        serialDevice = "/dev/ttyS0"
        baudRate = 9600
        stepsPerDegree = 1.0
        for o, a in opts:
                if o == "-p":
                        serialDevice = a
                if o == "-b":
                        baudRate = int(a)
                if o == "-s":
                        stepsPerDegree = float(a)
                else:
                        assert False, "Bad option given"
        if baudRate not in [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
                print "Bad baud rate specified!"
                sys.exit(2)
        serialPort = serial.Serial(serialDevice, baudrate = baudRate)

