# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 2019
Feature complete on Fri Aug 2 2019

This is a GUI to control 24 digital outputs and read 24 analog inputs using a
Raspberry Pi, 3x MCP3008 ADCs (bit-banged), and 3x 74HC595 shift registers 
for the purpose of maintaining and monitoring a photo-bioreactor with a 
circulating, temperature controlled water bath. Up to 5x DS18B20 Dallas 
1-Wire digital temperature sensors are supported, and the temperature data 
from these sensors are used to control a heater or chiller (user selectable). 
Seperate controls are given for the water pump and the light source. The GUI
 can write data to a file to record the state of all digital outputs, 
 temperatures, and the stored analog input readings. 5x user-customizable 
 buttons are provided. Each button can be assigned a file containing a script 
 which is executed when the button is pressed. Each script is written in a 
 "pseudo" G-code with the ability to adjust the delay time between each line
 and to jump to different lines in the script (eg: to loop back to the start 
 of the script). The scripts may be used to assign scripts to other buttons 
 and assign temperature sensors, limits, and modes (ie: a one-and-done initial
 configuration setup) OR the scripts can be used to run temperature, light, 
 and data collection routines that occur over an extended period of time. 

@author: lysholmc
"""

#import Tkinter as tk #for sone linux builds
import tkinter as tk 
import time
import RPi.GPIO as GPIO 
import glob
import statistics as stat
from tkinter import filedialog as tkfile 
#import tkFileDialog as tkfile #for some linux builds

#global recording
#global profileActive
global profileIn
global dataOut
global inFile
global digitalState
global SPICLK, SPIMISO, SPIMOSI, SPICS1, SPICS2, SPICS3
global latchPin, clockPin, dataPin
global temperatures, tMode

temperatures = [00.0 for n in range(5)]
recording = 0
profileActive = [0,0,0,0,0]
lampState = 0
tempControl = 0
minTemp = 0
maxTemp = 0
tMode = 1
profileIn = ['','','','','']
inFile = ['','','','','']
#digitalState = ['' for n in range(24)]
SPICLK = 16
SPIMISO = 13
SPIMOSI = 20
SPICS1 = 26
SPICS2 = 22
SPICS3 = 27
latchPin = 21 #Verify Pin assignment
clockPin = 16 #Same as SPICLK currently. For Shift Register #Verify Pin Assignment
dataPin = 20 #same as MOSI currently. Verify Pin assignment
outputEnablePin = 6
#tempDataPin = 4 #Must enable 1-wire protocol sudo raspi-config >interfacing options>1-Wire
#Temp data will be in /sys/bus/w1/devices/[28*]/w1_slave

GPIO.setmode(GPIO.BCM)

GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS1, GPIO.OUT)
GPIO.setup(SPICS2, GPIO.OUT)
GPIO.setup(SPICS3, GPIO.OUT)
GPIO.setup(latchPin, GPIO.OUT) #could comment out, double assigning with MISO/MOSI/SCK
GPIO.setup(clockPin, GPIO.OUT)
GPIO.setup(dataPin, GPIO.OUT)
GPIO.setup(outputEnablePin, GPIO.OUT)
GPIO.output(outputEnablePin, True) #Disable output immediately on startup

class ControlApp:
        def __init__(self, master):
            self.master = master
            master.title("Bioreactor Control v0.3.3")
            
            #DIGITAL OUTPUT WIDGETS
            self.airControlFrame = tk.LabelFrame(master, text="Digital Output")
            self.sendAirButton = tk.Button(self.airControlFrame, text="Send Output", width=12, command=self.sendAir)
            self.bgClear = root.cget("bg")
            self.airState = []
            self.digitalState = []
            for n in range(20):
                self.airState.append(tk.IntVar())
            for n in range(24):
                self.digitalState.append(tk.IntVar())
                self.digitalState[n] = 0;
            self.D1check = tk.Checkbutton(self.airControlFrame,text="D1", variable=self.airState[0])
            self.D2check = tk.Checkbutton(self.airControlFrame,text="D2", variable=self.airState[1])
            self.D3check = tk.Checkbutton(self.airControlFrame,text="D3", variable=self.airState[2])
            self.D4check = tk.Checkbutton(self.airControlFrame,text="D4", variable=self.airState[3])
            self.D5check = tk.Checkbutton(self.airControlFrame,text="D5", variable=self.airState[4])
            self.D6check = tk.Checkbutton(self.airControlFrame,text="D6", variable=self.airState[5])
            self.D7check = tk.Checkbutton(self.airControlFrame,text="D7", variable=self.airState[6])
            self.D8check = tk.Checkbutton(self.airControlFrame,text="D8", variable=self.airState[7])
            self.D9check = tk.Checkbutton(self.airControlFrame,text="D9", variable=self.airState[8])
            self.D10check = tk.Checkbutton(self.airControlFrame,text="D10", variable=self.airState[9])
            self.D11check = tk.Checkbutton(self.airControlFrame,text="D11", variable=self.airState[10])
            self.D12check = tk.Checkbutton(self.airControlFrame,text="D12", variable=self.airState[11])
            self.D13check = tk.Checkbutton(self.airControlFrame,text="D13", variable=self.airState[12])
            self.D14check = tk.Checkbutton(self.airControlFrame,text="D14", variable=self.airState[13])
            self.D15check = tk.Checkbutton(self.airControlFrame,text="D15", variable=self.airState[14])
            self.D16check = tk.Checkbutton(self.airControlFrame,text="D16", variable=self.airState[15])
            self.D17check = tk.Checkbutton(self.airControlFrame,text="D17", variable=self.airState[16])
            self.D18check = tk.Checkbutton(self.airControlFrame,text="D18", variable=self.airState[17])
            self.D19check = tk.Checkbutton(self.airControlFrame,text="D19", variable=self.airState[18])
            self.D20check = tk.Checkbutton(self.airControlFrame,text="D20", variable=self.airState[19])
            #self.D21check = tk.Checkbutton(self.airControlFrame,text="D21", variable=self.airState[20]) #CHILLER
            #self.D22check = tk.Checkbutton(self.airControlFrame,text="D22", variable=self.airState[21]) #HEATER
            #self.D23check = tk.Checkbutton(self.airControlFrame,text="D23", variable=self.airState[22]) #PUMP
            #self.D24check = tk.Checkbutton(self.airControlFrame,text="D24", variable=self.airState[23]) #LIGHT
            for n in range(20):
                self.digitalState[n] = self.airState[n].get()
            #DIGITAL OUTPUT LAYOUT
            self.D1check.grid(row=0,column=0,padx=5,sticky='w',pady=4)
            self.D2check.grid(row=0,column=1,padx=5,sticky='w')
            self.D3check.grid(row=0,column=2,padx=5,sticky='w')
            self.D4check.grid(row=1,column=0,padx=5,sticky='w',pady=4)
            self.D5check.grid(row=1,column=1,padx=5,sticky='w')
            self.D6check.grid(row=1,column=2,padx=5,sticky='w')
            self.D7check.grid(row=2,column=0,padx=5,sticky='w',pady=4)
            self.D8check.grid(row=2,column=1,padx=5,sticky='w')
            self.D9check.grid(row=2,column=2,padx=5,sticky='w')
            self.D10check.grid(row=3,column=0,padx=5,sticky='w',pady=4)
            self.D11check.grid(row=3,column=1,padx=5,sticky='w')
            self.D12check.grid(row=3,column=2,padx=5,sticky='w')
            self.D13check.grid(row=4,column=0,padx=5,sticky='w',pady=4)
            self.D14check.grid(row=4,column=1,padx=5,sticky='w')
            self.D15check.grid(row=4,column=2,padx=5,sticky='w')
            self.D16check.grid(row=5,column=0,padx=5,sticky='w',pady=4)
            self.D17check.grid(row=5,column=1,padx=5,sticky='w')
            self.D18check.grid(row=5,column=2,padx=5,sticky='w')
            self.D19check.grid(row=6,column=0,padx=5,sticky='w',pady=4)
            self.D20check.grid(row=6,column=1,padx=5,sticky='w')
            #self.D21check.grid(row=6,column=2,padx=5,sticky='w')
            #self.D22check.grid(row=7,column=0,padx=5,sticky='w',pady=4)
            #self.D23check.grid(row=7,column=1,padx=5,sticky='w')
            #self.D24check.grid(row=7,column=2,padx=5,sticky='w')
            self.sendAirButton.grid(row=8,columnspan=4, sticky='ew')
            
            #LIGHT CONTROL WIDGET
            self.lightControlFrame = tk.LabelFrame(master, text="Lamp Control (D24)")
            self.lightOnButton = tk.Button(self.lightControlFrame, text="ON", width=6, height=5, command=self.lightON)
            self.lightOffButton = tk.Button(self.lightControlFrame, text="OFF", width=6, relief="sunken", height=5, command=self.lightOFF)
#            self.digitalOptions = []            
#            for n in range(24):
#                self.digitalOptions.append(n+1)
#            self.lampChannelVar = tk.IntVar()
#            self.lampChannelVar.set(1)
#            self.lampChannel = tk.OptionMenu(self.lightControlFrame,self.lampChannelVar, *self.digitalOptions)
            
            #LIGHT CONTROL LAYOUT
            self.lightOnButton.grid(row=0,column=0, sticky='ew')   
            self.lightOffButton.grid(row=0,column=1, sticky='ew')  
#            self.lampChannel.grid(row=0,column=2)

            #PUMP CONTROL WIDGET
            self.pumpControlFrame = tk.LabelFrame(master, text="Pump Control (D23)")
            self.pumpOnButton = tk.Button(self.pumpControlFrame, text="ON", width=6, height=5, command=self.pumpON)
            self.pumpOffButton = tk.Button(self.pumpControlFrame, text="OFF", width=6, height=5,relief="sunken", command=self.pumpOFF)
#            self.pumpChannelVar = tk.IntVar()
#            self.pumpChannelVar.set(2)
#            self.pumpChannel = tk.OptionMenu(self.pumpControlFrame,self.pumpChannelVar, *self.digitalOptions)
            
            #PUMP CONTROL LAYOUT
            self.pumpOnButton.grid(row=0,column=0, sticky='e')
            self.pumpOffButton.grid(row=0,column=1,sticky='w')
#            self.pumpChannel.grid(row=0,column=2) 

            #SENSOR DISPLAY WIDGETS         
            self.sensorDispFrame= tk.LabelFrame(master, text="Sensor Readings")
            self.T1Label = tk.Label(self.sensorDispFrame,text="T1: "+str(temperatures[0]))
            self.T2Label = tk.Label(self.sensorDispFrame,text="T2: "+str(temperatures[1]))
            self.T3Label = tk.Label(self.sensorDispFrame,text="T3: "+str(temperatures[2]))
            self.T4Label = tk.Label(self.sensorDispFrame,text="T4: "+str(temperatures[3]))
            self.T5Label = tk.Label(self.sensorDispFrame,text="T5: "+str(temperatures[4]))
            self.base_dir = '/sys/bus/w1/devices/'
            self.tempOptions = glob.glob1(self.base_dir, '28*')
            self.tempOptions.append("               ")
            self.thermVar = []
            for n in range(5):
                #self.tempOptions.append("option "+str(n+1))
                self.thermVar.append(tk.StringVar())
            #self.thermVar[0].set(3)
            self.tempChannel1 = tk.OptionMenu(self.sensorDispFrame,self.thermVar[0], *self.tempOptions)
            self.tempChannel2 = tk.OptionMenu(self.sensorDispFrame,self.thermVar[1], *self.tempOptions)
            self.tempChannel3 = tk.OptionMenu(self.sensorDispFrame,self.thermVar[2], *self.tempOptions)
            self.tempChannel4 = tk.OptionMenu(self.sensorDispFrame,self.thermVar[3], *self.tempOptions)
            self.tempChannel5 = tk.OptionMenu(self.sensorDispFrame,self.thermVar[4], *self.tempOptions)
            self.dataRefreshButton = tk.Button(self.sensorDispFrame, text="Update", command=self.dataRefresh)
            self.analogData=[]
            self.updateFlag=[]
            for n in range(24):
                self.analogData.append("0000")
                self.updateFlag.append(tk.IntVar())
            
            self.A1check = tk.Checkbutton(self.sensorDispFrame,text=" A1: "+str(self.analogData[0]), variable=self.updateFlag[0])
            self.A2check = tk.Checkbutton(self.sensorDispFrame,text=" A2: "+str(self.analogData[1]), variable=self.updateFlag[1])
            self.A3check = tk.Checkbutton(self.sensorDispFrame,text=" A3: "+str(self.analogData[2]), variable=self.updateFlag[2])
            self.A4check = tk.Checkbutton(self.sensorDispFrame,text=" A4: "+str(self.analogData[3]), variable=self.updateFlag[3])
            self.A5check = tk.Checkbutton(self.sensorDispFrame,text=" A5: "+str(self.analogData[4]), variable=self.updateFlag[4])
            self.A6check = tk.Checkbutton(self.sensorDispFrame,text=" A6: "+str(self.analogData[5]), variable=self.updateFlag[5])
            self.A7check = tk.Checkbutton(self.sensorDispFrame,text=" A7: "+str(self.analogData[6]), variable=self.updateFlag[6])
            self.A8check = tk.Checkbutton(self.sensorDispFrame,text=" A8: "+str(self.analogData[7]), variable=self.updateFlag[7])
            self.A9check = tk.Checkbutton(self.sensorDispFrame,text=" A9: "+str(self.analogData[8]), variable=self.updateFlag[8])
            self.A10check = tk.Checkbutton(self.sensorDispFrame,text="A10: "+str(self.analogData[9]), variable=self.updateFlag[9])
            self.A11check = tk.Checkbutton(self.sensorDispFrame,text="A11: "+str(self.analogData[10]), variable=self.updateFlag[10])
            self.A12check = tk.Checkbutton(self.sensorDispFrame,text="A12: "+str(self.analogData[11]), variable=self.updateFlag[11])
            self.A13check = tk.Checkbutton(self.sensorDispFrame,text="A13: "+str(self.analogData[12]), variable=self.updateFlag[12])
            self.A14check = tk.Checkbutton(self.sensorDispFrame,text="A14: "+str(self.analogData[13]), variable=self.updateFlag[13])
            self.A15check = tk.Checkbutton(self.sensorDispFrame,text="A15: "+str(self.analogData[14]), variable=self.updateFlag[14])
            self.A16check = tk.Checkbutton(self.sensorDispFrame,text="A16: "+str(self.analogData[15]), variable=self.updateFlag[15])
            self.A17check = tk.Checkbutton(self.sensorDispFrame,text="A17: "+str(self.analogData[16]), variable=self.updateFlag[16])
            self.A18check = tk.Checkbutton(self.sensorDispFrame,text="A18: "+str(self.analogData[17]), variable=self.updateFlag[17])
            self.A19check = tk.Checkbutton(self.sensorDispFrame,text="A19: "+str(self.analogData[18]), variable=self.updateFlag[18])
            self.A20check = tk.Checkbutton(self.sensorDispFrame,text="A20: "+str(self.analogData[19]), variable=self.updateFlag[19])
            self.A21check = tk.Checkbutton(self.sensorDispFrame,text="A21: "+str(self.analogData[20]), variable=self.updateFlag[20])
            self.A22check = tk.Checkbutton(self.sensorDispFrame,text="A22: "+str(self.analogData[21]), variable=self.updateFlag[21])
            self.A23check = tk.Checkbutton(self.sensorDispFrame,text="A23: "+str(self.analogData[22]), variable=self.updateFlag[22])
            self.A24check = tk.Checkbutton(self.sensorDispFrame,text="A24: "+str(self.analogData[23]), variable=self.updateFlag[23])
            #SENSOR DISPLAY LAYOUT
            self.T1Label.grid(row=0,column=0,sticky='w')
            self.T2Label.grid(row=1,column=0,sticky='w')
            self.T3Label.grid(row=2,column=0,sticky='w')
            self.T4Label.grid(row=3,column=0,sticky='w')
            self.T5Label.grid(row=4,column=0,sticky='w')
            self.tempChannel1.grid(row=0,column=1)
            self.tempChannel2.grid(row=1,column=1)
            self.tempChannel3.grid(row=2,column=1)
            self.tempChannel4.grid(row=3,column=1)
            self.tempChannel5.grid(row=4,column=1)
            self.A1check.grid(row=0,column=2,sticky='w')
            self.A2check.grid(row=0,column=4,sticky='w')
            self.A3check.grid(row=0,column=6,sticky='w')
            self.A4check.grid(row=0,column=8,sticky='w')
            self.A5check.grid(row=0,column=10,sticky='w')
            self.A6check.grid(row=1,column=2,sticky='w')
            self.A7check.grid(row=1,column=4,sticky='w')
            self.A8check.grid(row=1,column=6,sticky='w')
            self.A9check.grid(row=1,column=8,sticky='w')
            self.A10check.grid(row=1,column=10,sticky='w')
            self.A11check.grid(row=2,column=2,sticky='w')
            self.A12check.grid(row=2,column=4,sticky='w')
            self.A13check.grid(row=2,column=6,sticky='w')
            self.A14check.grid(row=2,column=8,sticky='w')
            self.A15check.grid(row=2,column=10,sticky='w')
            self.A16check.grid(row=3,column=2,sticky='w')
            self.A17check.grid(row=3,column=4,sticky='w')
            self.A18check.grid(row=3,column=6,sticky='w')
            self.A19check.grid(row=3,column=8,sticky='w')
            self.A20check.grid(row=3,column=10,sticky='w')
            self.A21check.grid(row=4,column=2,sticky='w')
            self.A22check.grid(row=4,column=4,sticky='w')
            self.A23check.grid(row=4,column=6,sticky='w')
            self.A24check.grid(row=4,column=8,sticky='w')
            self.dataRefreshButton.grid(row=0,column=11,rowspan=5, padx=30, pady=5, sticky='nsew')
            
            #TEMP CONTROL PARAMETERS WIDGET
            self.tempControlFrame = tk.LabelFrame(master, text="Temperature Control (D22/D21)")
            self.lowerLimitLabel = tk.Label(self.tempControlFrame, text="Lower Limit (*C):")
            self.upperLimitLabel = tk.Label(self.tempControlFrame, text="Upper Limit (*C):")
            self.lowerLimitEntry = tk.Entry(self.tempControlFrame, width=5)
            self.upperLimitEntry = tk.Entry(self.tempControlFrame, width=5)
            self.tempDispLabel = tk.Label(self.tempControlFrame, text="0 *C")
            self.tempControlOnButton = tk.Button(self.tempControlFrame, text="ON", width=12, command=self.tempControlON)
            self.tempControlOffButton = tk.Button(self.tempControlFrame, text="OFF", width=12, relief="sunken", command=self.tempControlOFF)
            self.usingTemp = tk.StringVar()
            self.useTempLabel = tk.Label(self.tempControlFrame, textvariable=self.usingTemp, borderwidth=2)
#            self.heaterLabel = tk.Label(self.tempControlFrame, text="Heater:")
#            self.chillerLabel = tk.Label(self.tempControlFrame, text="Chiller:")
#            self.heaterChannelVar = tk.IntVar()
#            self.heaterChannelVar.set(3)
#            self.heaterChannel = tk.OptionMenu(self.tempControlFrame,self.heaterChannelVar, *self.digitalOptions)
#            self.chillerChannelVar = tk.IntVar()
#            self.chillerChannelVar.set(4)
#            self.chillerChannel = tk.OptionMenu(self.tempControlFrame,self.chillerChannelVar, *self.digitalOptions)
            
            #SUB-WIDGET: SELECT CONTROLLING SENSOR
            self.tempSensorSelectorFrame = tk.LabelFrame(self.tempControlFrame,text="Controlling Sensors")
            self.tempControlState = []
            for n in range(5):
                self.tempControlState.append(tk.IntVar())
            self.T1check = tk.Checkbutton(self.tempSensorSelectorFrame,text="T1", variable=self.tempControlState[0])
            self.T2check = tk.Checkbutton(self.tempSensorSelectorFrame,text="T2", variable=self.tempControlState[1])
            self.T3check = tk.Checkbutton(self.tempSensorSelectorFrame,text="T3", variable=self.tempControlState[2])
            self.T4check = tk.Checkbutton(self.tempSensorSelectorFrame,text="T4", variable=self.tempControlState[3])
            self.T5check = tk.Checkbutton(self.tempSensorSelectorFrame,text="T5", variable=self.tempControlState[4])
            #SUB-LAYOUT: SELECT CONTROLLING SENSOR
            self.T1check.grid(row=0,column=0)
            self.T2check.grid(row=0,column=1)
            self.T3check.grid(row=0,column=2)
            self.T4check.grid(row=0,column=3)
            self.T5check.grid(row=0,column=4)

            #SUB-WIDGET: HEAT/COOL
            self.tempModeFrame = tk.LabelFrame(self.tempControlFrame, text='Temperature Mode')
            self.tmodeVar = tk.IntVar()
            self.modeSelectHeat = tk.Radiobutton(self.tempModeFrame, text="Heat", variable=self.tmodeVar, value=1)
            self.modeSelectCool = tk.Radiobutton(self.tempModeFrame, text="Cool", variable=self.tmodeVar, value=0)
            #SUB-LAYOUT: HEAT/COOL
            self.modeSelectHeat.grid(row=0,column=0)
            self.modeSelectCool.grid(row=0,column=1)

            #SUB-WIDGET: REDUCTION MODE
            self.redModeFrame = tk.LabelFrame(self.tempControlFrame, text="Sensor Mode")
            self.modeVar = tk.IntVar()
            self.modeSelectMean = tk.Radiobutton(self.redModeFrame, text="Mean", variable=self.modeVar, value=1)
            self.modeSelectMedian = tk.Radiobutton(self.redModeFrame, text="Median", variable=self.modeVar, value=0)
            #SUB-LAYOUT: REDUCTION MODE
            self.modeSelectMean.grid(row=0,column=0)
            self.modeSelectMedian.grid(row=0,column=1)
            
            #TEMP CONTROL PARAMETERS LAYOUT
            self.tempSensorSelectorFrame.grid(row=1,column=0, columnspan=3, padx=10, sticky='nsew')
            self.tempControlOnButton.grid(row=0, column=0, pady=5, sticky='ew')
            self.tempControlOffButton.grid(row=0, column=1,columnspan=2, sticky='ew')
            self.lowerLimitLabel.grid(row=3,column=0, sticky='e')
            self.lowerLimitEntry.grid(row=3,column=1, sticky='w')
            self.upperLimitLabel.grid(row=4,column=0, sticky='e')
            self.upperLimitEntry.grid(row=4,column=1, sticky='w')
            self.redModeFrame.grid(row=2,column=0, columnspan=3, padx=10, sticky='ew')
            self.tempModeFrame.grid(row=5,column=0,columnspan=3, padx=10, pady=5, sticky='ew')
            self.useTempLabel.grid(row=3, column=2,rowspan=2, sticky='w')
            
            #DATA RECORDING WIDGETS
            self.dataFrame = tk.LabelFrame(master, text="Data Recording")
            self.dataFileButton = tk.Button(self.dataFrame, text ="Output File", command=self.findDataFile)
            self.dataFileEntry = tk.Entry(self.dataFrame, width=25)
            self.recordButton = tk.Button(self.dataFrame, text="Record", command=self.recordData)            
            #DATA RECORDING LAYOUT
            self.dataFileButton.grid(row=0,column=0,padx=5,pady=5)
            self.dataFileEntry.grid(row=0,column=1,padx=5,pady=5)
            self.recordButton.grid(row=1,column=0,columnspan=2,padx=5,pady=5,sticky='ew')
            
            #CUSTOM BUTTON WIDGET
            self.customFrame = tk.LabelFrame(master, text="Custom Functions")
            self.custom1Button =tk.Button(self.customFrame, text="Custom 1", command =self.custom1,width=20)
            self.custom1FileButton =tk.Button(self.customFrame, text="|", command=self.findCustom1File)
            self.custom2Button =tk.Button(self.customFrame, text="Custom 2", command =self.custom2,width=20)
            self.custom2FileButton =tk.Button(self.customFrame, text="|", command=self.findCustom2File)
            self.custom3Button =tk.Button(self.customFrame, text="Custom 3", command =self.custom3,width=20)
            self.custom3FileButton = tk.Button(self.customFrame, text="|", command=self.findCustom3File)
            self.custom4Button =tk.Button(self.customFrame, text="Custom 4", command =self.custom4,width=20)
            self.custom4FileButton= tk.Button(self.customFrame, text="|", command =self.findCustom4File)
            #CUSTOM BUTTON LAYOUT
            #self.numTemps.grid(row=0,column=0)
            self.custom1Button.grid(row=0,column=0,columnspan=3)
            self.custom2Button.grid(row=1,column=0,columnspan=3)
            self.custom3Button.grid(row=2,column=0,columnspan=3)
            self.custom4Button.grid(row=3,column=0,columnspan=3)
            self.custom1FileButton.grid(row=0,column=4)
            self.custom2FileButton.grid(row=1,column=4)
            self.custom3FileButton.grid(row=2,column=4)
            self.custom4FileButton.grid(row=3,column=4)

            #PROFILE LOADING WIDGET
            self.profileFrame = tk.LabelFrame(master, text="Load Profile")
            self.loadProfileButton = tk.Button(self.profileFrame, text="Load Profile", command=self.findProfile)
            self.profileEntry= tk.Entry(self.profileFrame, width=25)
            self.executeButton = tk.Button(self.profileFrame, text="Execute", command=self.executeProfile)
            #PROFILE LOADING LAYOUT
            self.loadProfileButton.grid(row=0,column=0,padx=5,pady=5)
            self.profileEntry.grid(row=0,column=1,padx=5,pady=5)
            self.executeButton.grid(row=1,column=0,columnspan=2,padx=5,pady=5,stick='ew')
            
            #MASTER LAYOUT
            self.airControlFrame.grid(row=0,column=0,padx=10,pady=10,ipady=2,rowspan=2,sticky='nesw')
            self.lightControlFrame.grid(row=1,column=2,padx=10,pady=10,ipady=2, sticky='nesw')
            self.pumpControlFrame.grid(row=2,column=2,padx=10,pady=10,ipady=2,sticky='nesw')
            self.sensorDispFrame.grid(row=0,column=1,padx=10,pady=10,rowspan=1,columnspan=3,sticky='nesw')
            self.dataFrame.grid(row=1,column=3,padx=10,pady=10,ipady=5, sticky='nesw')
            self.profileFrame.grid(row=2,column=3,padx=10,pady=10,ipady=5,sticky='nesw')
            self.tempControlFrame.grid(row=1, column=1, padx=10, columnspan=1, rowspan = 2, ipady=5, pady=10,sticky='nesw')
            self.customFrame.grid(row=2,column=0, padx=10,pady=10, rowspan=1, sticky='nesw')
            #self.inputXYFrame.grid(row=1,column=0,padx=10, pady=10,ipady=5,sticky='new')
            
            #DEFAULT SETTINGS
            self.tmodeVar.set(1) #HEAT - set to 0 for COOL
            self.modeVar.set(0) #MEDIAN - set to 1 for MEAN
            self.lowerLimitEntry.insert(0,'31.5')
            self.upperLimitEntry.insert(0,'33.5')
            self.thermVar[0].set("               ") #Temp Sensor 1
            self.thermVar[1].set("               ") #Temp Sensor 2
            self.thermVar[2].set("               ") #Temp Sensor 3
            self.thermVar[3].set("               ") #Temp Sensor 4
            self.thermVar[4].set("               ") #Temp Sensor 5

        def findProfile(self):
            global profileIn
            profileIn[0] = tkfile.askopenfilename()
            self.profileEntry.delete(0,'end')
            self.profileEntry.insert(0,profileIn[0])
            self.profileEntry.xview('end')

        def findDataFile(self):
            global dataOut            
            dataOut = tkfile.asksaveasfilename()
            self.dataFileEntry.delete(0,'end')
            self.dataFileEntry.insert(0,dataOut)
            self.dataFileEntry.xview('end')
        
        def sendAir(self):
            global latchPin, clockPin
            #global digitalState
            n = 0
            while n < 20: #or 21 if no chiller
                if (self.airState[n].get()):
                    print("Channel " +str(n+1)+ " is ON")
                n += 1
            for n in range(20):
                self.digitalState[n] = self.airState[n].get()
            self.shiftOut()                
            
        def lightON(self):
            global latchPin, clockPin
            #global digitalState
            #lampState = 1
            self.lightOnButton.config(relief="sunken")
            self.lightOffButton.config(relief="raised")
            #self.airState[23] = 1
            self.digitalState[23] = 1
            self.shiftOut()
#            print(self.numTempVar.get())            
#            if self.numTempVar.get() == 1:
#                self.air1check.config(state="disabled")
            
        def lightOFF(self):
            #global digitalState
            self.lightOffButton.config(relief="sunken")
            self.lightOnButton.config(relief="raised")
            #self.airState[23] = 0 #Doesn't really do anything
            self.digitalState[23] = 0
            self.shiftOut()
            
        def tempControlON(self):
            global tempControl, minTemp, maxTemp, tMode
            minTemp = float(self.lowerLimitEntry.get())
            maxTemp = float(self.upperLimitEntry.get())
            tMode = float(self.tmodeVar.get())
            tempControl = 1
            self.tempControlOnButton.config(relief="sunken")
            self.tempControlOffButton.config(relief="raised")
            
        def tempControlOFF(self):
            global tempControl
            #TO DO: set heater gpio low
            tempControl = 0
            self.digitalState[20] = 0
            self.digitalState[21] = 0 #Is this same or better than just " =0"?
            self.shiftOut()
            self.tempControlOffButton.config(relief="sunken")
            self.tempControlOnButton.config(relief="raised")
            
        def pumpON(self):
            #global digitalState
            self.pumpOnButton.config(relief="sunken")
            self.pumpOffButton.config(relief="raised")
            self.digitalState[22] = 1
            self.shiftOut()
        
        def pumpOFF(self):
            #global digitalState
            self.pumpOffButton.config(relief="sunken")
            self.pumpOnButton.config(relief="raised")
            self.digitalState[22] = 0
            self.shiftOut()
        
        def recordData(self):
            global recording
            global dataOut
            recording = not(recording)
            if recording:
                self.recordButton.config(relief="sunken", bg="red", fg="white")
                dataOut = self.dataFileEntry.get()                
                if dataOut == '':
                    print("No File Specified")
                    recording = 0
                    self.recordButton.config(relief="raised",bg=self.bgClear,fg="black")
                    return
            else:
                self.recordButton.config(relief="raised", bg=self.bgClear, fg="black")
                    
        def executeProfile(self):
            global profileActive
            global profileIn
            global inFile
            profileActive[0] = not(profileActive[0])
            if profileActive[0]:
                self.executeButton.config(relief="sunken", bg="red", fg="white")
                profileIn[0] = self.profileEntry.get()
                if profileIn[0] == '':
                    print("No File Specified")
                    profileActive[0] = 0
                    self.executeButton.config(relief="raised",bg=self.bgClear,fg="black")
                    return
                inFile[0] = open(profileIn[0],'r')
            else: 
                self.executeButton.config(relief="raised", bg=self.bgClear, fg="black")
                inFile[0].close()
       
        def dataRefresh(self): 
            for n in range(24):
                if self.updateFlag[n].get():                
                    if n <= 8:
                        self.analogData[n] = self.readadc(n,SPICLK,SPIMOSI,SPIMISO,SPICS1)
                    elif n <= 16:
                        self.analogData[n] = self.readadc(n-8,SPICLK,SPIMOSI,SPIMISO,SPICS2)
                    elif n <= 24:
                        self.analogData[n] = self.readadc(n-16,SPICLK,SPIMOSI,SPIMISO,SPICS3)
                        
            self.A1check.config(text=" A1: "+str(self.analogData[0]).zfill(4))
            self.A2check.config(text=" A2: "+str(self.analogData[1]).zfill(4))
            self.A3check.config(text=" A3: "+str(self.analogData[2]).zfill(4))
            self.A4check.config(text=" A4: "+str(self.analogData[3]).zfill(4))
            self.A5check.config(text=" A5: "+str(self.analogData[4]).zfill(4))
            self.A6check.config(text=" A6: "+str(self.analogData[5]).zfill(4))
            self.A7check.config(text=" A7: "+str(self.analogData[6]).zfill(4))
            self.A8check.config(text=" A8: "+str(self.analogData[7]).zfill(4))
            self.A9check.config(text=" A9: "+str(self.analogData[8]).zfill(4))
            self.A10check.config(text="A10: "+str(self.analogData[9]).zfill(4))
            self.A11check.config(text="A11: "+str(self.analogData[10]).zfill(4))
            self.A12check.config(text="A12: "+str(self.analogData[11]).zfill(4))
            self.A13check.config(text="A13: "+str(self.analogData[12]).zfill(4))
            self.A14check.config(text="A14: "+str(self.analogData[13]).zfill(4))
            self.A15check.config(text="A15: "+str(self.analogData[14]).zfill(4))
            self.A16check.config(text="A16: "+str(self.analogData[15]).zfill(4))
            self.A17check.config(text="A17: "+str(self.analogData[16]).zfill(4))
            self.A18check.config(text="A18: "+str(self.analogData[17]).zfill(4))
            self.A19check.config(text="A19: "+str(self.analogData[18]).zfill(4))
            self.A20check.config(text="A20: "+str(self.analogData[19]).zfill(4))
            self.A21check.config(text="A21: "+str(self.analogData[20]).zfill(4))
            self.A22check.config(text="A22: "+str(self.analogData[21]).zfill(4))
            self.A23check.config(text="A23: "+str(self.analogData[22]).zfill(4))
            self.A24check.config(text="A24: "+str(self.analogData[23]).zfill(4))
            
            n = 0
            while n < len(self.updateFlag):
                if (self.updateFlag[n].get()):
                    print("Channel " +str(n+1)+ " is Updated")
                n += 1
        
        def findCustom1File(self):
            global profileIn
            profileIn[1] = tkfile.askopenfilename()
            self.custom1FileButton.config(relief='sunken')
            if profileIn[1] == '':
                self.custom1FileButton.config(relief='raised')
                self.custom1Button.config(text='Custom 1')
            else:
                self.renameButton(1,profileIn[1])
        
        def custom1(self):
            global profileActive
            global profileIn
            global inFile
            profileActive[1] = not(profileActive[1])
            if profileActive[1]:
                self.custom1Button.config(relief="sunken", bg="red", fg="white")
                if profileIn[1] == '':
                    print("No File Specified")
                    profileActive[1] = 0
                    self.custom1Button.config(relief="raised",bg=self.bgClear,fg="black")
                    return
                inFile[1] = open(profileIn[1],'r')
            else: 
                self.custom1Button.config(relief="raised", bg=self.bgClear, fg="black")
                inFile[1].close()

        def findCustom2File(self):
            global profileIn
            profileIn[2] = tkfile.askopenfilename()
            self.custom2FileButton.config(relief='sunken')
            if profileIn[2] == '':
                self.custom2FileButton.config(relief='raised')
                self.custom2Button.config(text='Custom 2')
            else:
                app.renameButton(2,profileIn[2])
        
        def custom2(self):
            global profileActive
            global profileIn
            global inFile
            profileActive[2] = not(profileActive[2])
            if profileActive[2]:
                self.custom2Button.config(relief="sunken", bg="red", fg="white")
                if profileIn[2] == '':
                    print("No File Specified")
                    profileActive[2] = 0
                    self.custom2Button.config(relief="raised",bg=self.bgClear,fg="black")
                    return
                inFile[2] = open(profileIn[2],'r')
            else: 
                self.custom2Button.config(relief="raised", bg=self.bgClear, fg="black")
                inFile[2].close()

        def findCustom3File(self):
            global profileIn
            profileIn[3] = tkfile.askopenfilename()
            self.custom3FileButton.config(relief='sunken')
            if profileIn[3] == '':
                self.custom3FileButton.config(relief='raised')
                self.custom3Button.config(text='Custom 3')
            else:
                app.renameButton(3,profileIn[3])
        
        def custom3(self):
            global profileActive
            global profileIn
            global inFile
            profileActive[3] = not(profileActive[3])
            if profileActive[3]:
                self.custom3Button.config(relief="sunken", bg="red", fg="white")
                if profileIn[3] == '':
                    print("No File Specified")
                    profileActive[3] = 0
                    self.custom3Button.config(relief="raised",bg=self.bgClear,fg="black")
                    return
                inFile[3] = open(profileIn[3],'r')
            else: 
                self.custom3Button.config(relief="raised", bg=self.bgClear, fg="black")
                inFile[3].close()
            
        def findCustom4File(self):
            global profileIn
            profileIn[4] = tkfile.askopenfilename()
            self.custom4FileButton.config(relief='sunken')
            if profileIn[4] == '':
                self.custom4FileButton.config(relief='raised')
                self.custom4Button.config(text='Custom 4')
            else:
                app.renameButton(4,profileIn[4])
        
        def custom4(self):
            global profileActive
            global profileIn
            global inFile
            profileActive[4] = not(profileActive[4])
            if profileActive[4]:
                self.custom4Button.config(relief="sunken", bg="red", fg="white")
                if profileIn[4] == '':
                    print("No File Specified")
                    profileActive[4] = 0
                    self.custom4Button.config(relief="raised",bg=self.bgClear,fg="black")
                    return
                inFile[4] = open(profileIn[4],'r')
            else: 
                self.custom4Button.config(relief="raised", bg=self.bgClear, fg="black")
                inFile[4].close()
                
        def renameButton(self, button, fileName):
            newName_list = fileName.split('/')
            if newName_list[-1][-4] == '.':
                newName = newName_list[-1][:-4]
            else:
                newName = newName_list[-1]
            if button == 0:
                pass #Don't rename EXECUTE button, file name is in EntryBox
                #app.executeButton.config(text=newName)
            elif button == 1:
                app.custom1Button.config(text=newName)
            elif button == 2:
                app.custom2Button.config(text=newName)
            elif button == 3:
                app.custom3Button.config(text=newName)
            elif button == 4:
                app.custom4Button.config(text=newName)
        
        #Function for bit-banging MCP3008
        def readadc(self, adcnum, clockpin, mosipin, misopin, cspin):
            if ((adcnum > 7) or (adcnum < 0)):
                    return -1
            GPIO.output(cspin, True)
     
            GPIO.output(clockpin, False)  # start clock low
            GPIO.output(cspin, False)     # bring CS low
     
            commandout = adcnum
            commandout |= 0x18  # start bit + single-ended bit
            commandout <<= 3    # we only need to send 5 bits here
            for i in range(5):
                    if (commandout & 0x80):
                            GPIO.output(mosipin, True)
                    else:
                            GPIO.output(mosipin, False)
                    commandout <<= 1
                    GPIO.output(clockpin, True)
                    GPIO.output(clockpin, False)
     
            adcout = 0
            # read in one empty bit, one null bit and 10 ADC bits
            for i in range(12):
                    GPIO.output(clockpin, True)
                    GPIO.output(clockpin, False)
                    adcout <<= 1
                    if (GPIO.input(misopin)):
                            adcout |= 0x1
     
            GPIO.output(cspin, True)
            
            adcout >>= 1       # first bit is 'null' so drop it
            return adcout
        
        #Function for 74HC595 shift register (bit-banged)
        def shiftOut(self):
            global latchPin, dataPin, clockPin, outputEnablePin
            GPIO.output(dataPin, False)
            GPIO.output(clockPin, False)
            #GPIO.output(outputEnablePin, False) #OUTPUT ENABLED AFTER STARTUP
            
            GPIO.output(latchPin, False)
            for n in range(len(self.digitalState)):
                GPIO.output(clockPin, False)
                GPIO.output(dataPin, self.digitalState[n])
                GPIO.output(clockPin, True)
            GPIO.output(latchPin, True)
            #GPIO.output(outputEnablePin, True)
        
        #from Adafruit example code for DS18B20 sensors

root = tk.Tk()
app = ControlApp(root)

for n in range(len(app.digitalState)):
        app.digitalState[n] = 0
app.shiftOut()
GPIO.output(outputEnablePin, False)


timeInitial = time.time()
timeLast_data = timeInitial
timeLast_profile = [timeInitial, timeInitial, timeInitial, timeInitial, timeInitial]
timeLast_tempControl = timeInitial
profileInterval = [0.5, 0.5, 0.5, 0.5, 0.5] #Time between profile command executions
def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device_file):
#    global temperatures
    lines = read_temp_raw(device_file)
#            while lines[0].strip()[-3:] != 'YES':
#                time.sleep(0.05)
#                lines = self.read_temp_raw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        #temp_f = temp_c * 9.0 / 5.0 + 32.0 #Uncomment this line to return in deg F
        return temp_c#, temp_f
def tasks():
    global timeLast_data
    global timeLast_profile
    global timeLast_tempControl
    global profileInterval
    global inFile
    global dataOut
    global SPICLK, SPIMISO, SPIMOSI, SPICS1, SPICS2, SPICS3
    global temperatures

    if recording:
        if time.time() - timeLast_data > 5: #Record data every 5 seconds
            outFile = open(dataOut,'a')
            outString = "{0:.1f}".format(time.time())
            
            for n in range(5): #Record T1-5
                outString += " T"+str(n+1)+":"+str(temperatures[n]) + ","
            for n in range(24): #Record D1-D20 + Chiller, Heater, Pump, Lamp
                outString += " D"+str(n+1)+":"+ str(app.digitalState[n]) + ","
            for n in range(24): #Record A1-A24
                outString += " A"+str(n+1)+":"+ str(app.analogData[n]) + ","
            
            outString = outString[:-1] #remove trailing ","
            outString += '\n'
            outFile.write(outString)
            outFile.close()
            timeLast_data = time.time()
    #TEMPERATURE
    if time.time() - timeLast_tempControl > 3: #Update temps every 3 seconds 
        #UPDATE ALL TEMPERATURES PER DROPDOWN MENU
        for n in range(5):
            if app.thermVar[n].get() != "               ":
                device_file = app.base_dir + app.thermVar[n].get() + '/w1_slave'
                temperatures[n] = read_temp(device_file)
            else:
                temperatures[n] = 0.0
        app.T1Label.config(text="T1: "+ "{0:.2f}".format(temperatures[0]))
        app.T2Label.config(text="T2: "+ "{0:.2f}".format(temperatures[1]))
        app.T3Label.config(text="T3: "+ "{0:.2f}".format(temperatures[2]))
        app.T4Label.config(text="T4: "+"{0:.2f}".format(temperatures[3]))
        app.T5Label.config(text="T5: "+"{0:.2f}".format(temperatures[4]))
        #REDUCE AND DISPLAY in TEMP CONTROL FRAME, REGARDLESS OF ON/OFF
        tempSum = 0 
        numUsed = 0
        tempList = []
        if app.modeVar.get(): #MEAN
            for n in range(len(temperatures)):
                if int(app.tempControlState[n].get()):
                    numUsed += 1    
                    tempSum += temperatures[n]
            if numUsed: #if no sensors selected, prevent div/0
                currentTemp = tempSum/numUsed
            else:
                currentTemp = 0.0
        else: #MEDIAN
            for n in range(len(temperatures)):
                if int(app.tempControlState[n].get()):
                    tempList.append(temperatures[n])
            if tempList:  #Can't do median of empty list, if none selected
                currentTemp = stat.median(tempList)
            else:
                currentTemp = 0.0
            app.usingTemp.set(str(currentTemp))       
        
        if tempControl:
            if tMode: #HEATING
                lastState = int(app.digitalState[21])
                newState = lastState
                if currentTemp > maxTemp:
                    newState = 0 #HEATER OFF 
                elif currentTemp < minTemp:
                    newState = 1 #HEATER ON
                if lastState != newState: #only bother SHIFTING if state does not need to change
                    app.digitalState[21] = newState
                    app.shiftOut()
            else: #CHILLING
                lastState = int(app.digitalState[20])
                newState = lastState
                if currentTemp > maxTemp:
                    newState = 1 #CHILLER ON 
                elif currentTemp < minTemp:
                    newState = 0 #CHILLER OFF
                if lastState != newState: #only bother SHIFTING if state does not need to change
                    app.digitalState[20] = newState
                    app.shiftOut()
        timeLast_tempControl = time.time()
    for n in range(5): #CHECK FOR ANY ACTIVE PROFILES AND HANDLE IF TRUE
        if profileActive[n]:
            if time.time() - timeLast_profile[n] > profileInterval[n]:
                currentLine = inFile[n].readline()
                if currentLine:
                    currentLine = currentLine.rstrip('\n')
                    currentLine = currentLine.split(';', 1) #splits at the first occurance of ';'
                    currentLine[0] = currentLine[0].upper()
                    currentLine = ';'.join(currentLine)
                    lcv = 1
                    while lcv < len(currentLine): #add a space before every letter encountered
                        if ((currentLine[lcv].isalpha()) and (currentLine[lcv-1] !=' ')):
                            currentLine = currentLine[:lcv]+' '+currentLine[lcv:]
                        if (currentLine[lcv] == ';'):
                            break
                        lcv += 1
                            
                    currentLine = currentLine.split()
                    #print(currentLine)
                    if (not currentLine): #THIS MEANS IT WASN'T EMPTY, BUT BECAME EMPTY WITH THE STRIP()
                        currentLine += ' ' #ADD A NONFUNTIONAL SPACE TO PAD THE EMPTINESS
                    currentWord=0
                    if currentLine[currentWord] == 'G0': #set command interval
                        currentWord += 1
                        lastValid = 'G0'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "I"):
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                profileInterval[n] = float(currentLine[currentWord][1:]) #update profile command execution interval
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1
                            
                    elif currentLine[currentWord] == 'G1': #Digital Output Control
                        currentWord += 1
                        lastValid = 'G1'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "T"): #SELECT Channel NUMBER
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                tubeNum = int(currentLine[currentWord][1:]) #Set tube number
                            
                            elif (currentLine[currentWord][0] == "A"): #SELECT Output ON/OFF
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                active = int(currentLine[currentWord][1:])
                                if active:
                                    app.airState[tubeNum-1].set(1)

                                else:
                                    app.airState[tubeNum-1].set(0)
                                       
                            elif (currentLine[currentWord][0] == "X"): #SEND Output
    #                            if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
    #                                currentLine[currentWord] += currentLine[currentWord+1]
    #                                currentLine[currentWord+1] = ' '
                                app.sendAir() #Send Air according to airState variable
    
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1
                      
                    elif currentLine[currentWord] == 'G2': #Lamp Control
                        currentWord += 1
                        lastValid = 'G2'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "X"): #ACTIVATE/DEACTIVATE 0/1
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                if int(currentLine[currentWord][1:]):
                                    app.lightON()
                                else:
                                    app.lightOFF()
                                        
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1
                            
                    elif currentLine[currentWord] == 'G3': #Temperature Control
                        currentWord += 1
                        lastValid = 'G3'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "X"): #ACTIVATE/DEACTIVATE 0/1
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                if int(currentLine[currentWord][1:]):
                                    app.tempControlON()
                                else:
                                    app.tempControlOFF()
                            elif (currentLine[currentWord][0] == "T"): #SELECT Channel NUMBER
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                tubeNum = int(currentLine[currentWord][1:]) #Set tube number
                            
                            elif (currentLine[currentWord][0] == "A"): #SELECT Output ON/OFF
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                active = int(currentLine[currentWord][1:])
                                if active:
                                    app.tempControlState[tubeNum-1].set(1)
                                else:
                                    app.tempControlState[tubeNum-1].set(0)
                                    
                            elif (currentLine[currentWord][0] == "H"): #SET HEAT/COOL 1/0
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                active = int(currentLine[currentWord][1:])
                                if active:
                                    app.tmodeVar.set(1)
                                else:
                                    app.tmodeVar.set(0)
                            elif (currentLine[currentWord][0] == "R"): #SET MEAN/MEDIAN 0/1
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                active = int(currentLine[currentWord][1:])
                                if active:
                                    app.modeVar.set(1)
                                else:
                                    app.modeVar.set(0)
                            elif (currentLine[currentWord][0] == "U"): #SET Upper limit
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                limit = float(currentLine[currentWord][1:])
                                app.upperLimitEntry.delete(0,'end')
                                app.upperLimitEntry.insert(0,limit)
                            elif (currentLine[currentWord][0] == "L"): #SET Lower limit
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                limit = float(currentLine[currentWord][1:])
                                app.lowerLimitEntry.delete(0,'end')
                                app.lowerLimitEntry.insert(0,limit)

                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1
                            
                    elif currentLine[currentWord] == 'G4': #Recorder Control
                        currentWord += 1
                        lastValid = 'G4'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "X"): #ACTIVATE/DEACTIVATE

                                app.recordData()
                          
                            elif (currentLine[currentWord][0] == "S"): #SAVE FILE LOCATION
                                print(currentLine)
                                #currentLine = currentLine.strip(';')
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                dataOut = currentLine[currentWord][2:] #Set file location
                                app.dataFileEntry.delete(0,'end')
                                app.dataFileEntry.insert(0,dataOut)
                                app.dataFileEntry.xview('end')
                            
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1
                            
                    elif currentLine[currentWord] == 'G5': #Profile Execution Control
                        currentWord += 1
                        lastValid = 'G5'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "X"): #ACTIVATE/DEACTIVATE 0-4
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                if int(currentLine[currentWord][1:]) == 0:
                                    app.executeProfile()
                                elif int(currentLine[currentWord][1:]) == 1:
                                    app.custom1()
                                elif int(currentLine[currentWord][1:]) == 2:
                                    app.custom2()                                    
                                elif int(currentLine[currentWord][1:]) == 3:
                                    app.custom3()
                                elif int(currentLine[currentWord][1:]) == 4:
                                    app.custom4()
                                else:
                                    print("Invalid Command. Please specify profile G5 X0-4.")

                            if (currentLine[currentWord][0] == "S"): #LOAD PROFILE LOCATION 0-4
                                print(currentLine)
                                #currentLine = currentLine.strip(';')
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                tubeNum = int(currentLine[currentWord][1:])
                                if tubeNum == ';':
                                    print("Invalid Command. Must specify profile G5 S0-4.")
                                    break
                                profileIn[tubeNum] = currentLine[currentWord][3:]
                                
                                if tubeNum == 0:
                                    app.profileEntry.delete(0,'end')
                                    app.profileEntry.insert(0,profileIn[0])
                                    app.profileEntry.xview('end')
                                elif tubeNum == 1:
                                    app.custom1FileButton.config(relief='sunken')
                                elif tubeNum == 2:
                                    app.custom2FileButton.config(relief='sunken')
                                elif tubeNum == 3:
                                    app.custom3FileButton.config(relief='sunken')
                                elif tubeNum == 4:
                                    app.custom4FileButton.config(relief='sunken')
                                
                                app.renameButton(tubeNum,profileIn[tubeNum]) 
                                
                            elif (currentLine[currentWord][0] == "L"): #GO TO LINE. Affects current profile only. 
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                line = int(currentLine[currentWord][1:])
                                inFile[n].seek(line) #in theory, if we adjust 'n' we could also change other profiles, but we need to check if they are open
                                
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1

                    elif currentLine[currentWord] == 'G6': #DATA COLLECTION AND REFRESH //NOT RECORDING
                        currentWord += 1
                        lastValid = 'G6'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "X"): #Send Analog Data Refresh Command
                                app.dataRefresh()
                            
                            elif (currentLine[currentWord][0] == "T"):
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                tubeNum = int(currentLine[currentWord][1:]) #Set channel number
                            
                            elif (currentLine[currentWord][0] == "A"): #SELECT UPDATE ON/OFF
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                active = int(currentLine[currentWord][1:])
                                if active:
                                    app.updateFlag[tubeNum-1].set(1)
                                else:
                                    app.updateFlag[tubeNum-1].set(0)    
                            
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1                                
                
                    elif currentLine[currentWord] == 'G7': #Pump Control
                        currentWord += 1
                        lastValid = 'G7'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "X"): #ACTIVATE/DEACTIVATE 0/1
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                if int(currentLine[currentWord][1:]):
                                    app.pumpON()
                                else:
                                    app.pumpOFF()
                                        
                            elif (currentLine[currentWord][0] == ";"):
                                break
                            currentWord += 1
                
                    elif currentLine[currentWord] == 'G8': #Temp Sensor Setup
                        currentWord += 1
                        lastValid = 'G8'
                        while currentWord < len(currentLine):
                            if (currentLine[currentWord][0] == "S"): #Assign Temp Sensor to channel
                                if (len(currentLine[currentWord]) == 1): #This means that the value is in the next Word
                                    currentLine[currentWord] += currentLine[currentWord+1]
                                    currentLine[currentWord+1] = ' '
                                tubeNum = int(currentLine[currentWord][1:])
                                if tubeNum == ';':
                                    print("Invalid Command. Must specify channel G8 S1-5.")
                                    break
                                app.thermVar[tubeNum].set(currentLine[currentWord][3:])     
                                    
                else:
                    if n == 0:
                        app.executeProfile() 
                    elif n == 1:
                        app.custom1()
                    elif n == 2:
                        app.custom2()
                    elif n == 3:
                        app.custom3()
                    elif n == 4:
                        app.custom4()
                    profileInterval[n] = 0.5 #reset profile interval to forget last interval in program
                
                timeLast_profile[n] = time.time()
   
    root.after(200,tasks)           

root.after(200, tasks())
root.mainloop()



