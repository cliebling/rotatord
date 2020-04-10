#!/usr/bin/python 
from __future__ import division
import serial
import getopt
import sys

# Rot2Prog implementation (c) 2020 C. Liebling W3PZ crlieb@swbell.net
# Distributed under the GPLv2

CmdStop = 0x0F
CmdStatus = 0x1F
CmdSet = 0x2F

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
        print "Stepping azimuth clockwise: ", steps
        pass

def stepAzCCW(steps):
        print "Stepping azimuth counterclockwise: ", steps
        pass

def stepElCW(steps):
        print "Stepping elevation clockwise: ", steps
        pass

def stepElCCW(steps):
        print "Stepping elevation counterclockwise: ", steps
        pass

def moveRotatorTo(azimuth, newAzimuth, elevation, newElevation, stepsPerDegree):
        azimuthDegrees = 0
        elevationDegrees = 0
        azimuthSteps = 0
        elevationSteps = 0
        azimuthDegrees = newAzimuth - azimuth
        elevationDegrees = newElevation - elevation
        azimuthSteps = abs(azimuthDegrees * stepsPerDegree)
        elevationSteps = abs(elevationDegrees * stepsPerDegree)
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

def printUsage():
        print """-h: This help menu
                 -p: path to serial device
                 -s: steps per degree that hamlib expects
                 -b baud rate\n"""

def main():
        global CmdStop
        global CmdStatus
        global CmdSet
        try:
                opts, args = getopt.getopt(sys.argv[1:], "p:s:b:h")
        except getopt.GetoptError as err:
                sys.exit(2)
        print "Going to parse options"
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
        serialPort = serial.Serial(serialDevice, baudrate = baudRate)
        while True:        
                command = waitForCommand(serialPort)
                print "Got a command"
                print command
                if checkCommand(command) == False:
                        continue
                if getCmdType(command) == CmdStop:
                        stopRotator()
                if getCmdType(command) == CmdStatus:
                        sendStatus(serialPort, azimuth, elevation, PH, PV)
                if getCmdType(command) == CmdSet:
                        print "Got a set command"
                        newAzimuth = calcAzimuth(command)
                        newElevation = calcElevation(command)
                        print "Setting Azimuth to ", newAzimuth
                        print "Setting Elevation to ", newElevation
                        moveRotatorTo(azimuth, newAzimuth, elevation, newElevation, stepsPerDegree)

if __name__ == "__main__":
        main()
