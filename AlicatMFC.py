import serial
import alicat
import os
from time import sleep
import time
from alicat import FlowController
import pandas as pd

#DISCLAIMER: DO NOT RENAME FUNCTIONS UNLESS YOU ARE PREPARED TO CHANGE THE LABVIEW PYTHON NODES

#convert MicroAeth string data to a float 
def toFloat(string):
    try:
        return float(string)
    #account for null value
    except TypeError and ValueError:
        return 0

    
#get MA350 data and export an array of necessary values to LabVIEW
def getMicroAethData():
    #read first byte

    received_data = aeth_ser.read()
    sleep(0.04)

    #number of bytes left in the bffer
    data_left = aeth_ser.inWaiting()
    #add left over bytes and decode into a string
    try:
        received_data = (received_data+ aeth_ser.read(data_left)).decode()

        #split the received data into na array
        arr_aeth_data = received_data.split(',')

        #check that the serial data is actually the MA350 data we want
        if arr_aeth_data[0][0:5] == "MA350" and len(arr_aeth_data) >= 70:
            #timebase, tape position, flow setpoint, flow total, sample temp, sample rh, sample dewpoit, uv atn1, uv atn2, ir atn1, ir atn2, ir bc1, ir bcc, mode
            return [
                toFloat(arr_aeth_data[10]),
                toFloat(arr_aeth_data[16]),
                toFloat(arr_aeth_data[17]),
                toFloat(arr_aeth_data[18]),
                toFloat(arr_aeth_data[21]),
                toFloat(arr_aeth_data[22]),
                toFloat(arr_aeth_data[23]),
                toFloat(arr_aeth_data[30]),
                toFloat(arr_aeth_data[31]),
                toFloat(arr_aeth_data[54]),
                toFloat(arr_aeth_data[55]),
                toFloat(arr_aeth_data[69]),
                toFloat(arr_aeth_data[71]),
                0
            ]
        elif len(arr_aeth_data)>=50 and arr_aeth_data[2] == "2022" and arr_aeth_data[5] == "2022":
            #if using PAX:
            return [
                0,
                0,
                0,
                0,
                toFloat(arr_aeth_data[24]),
                toFloat(arr_aeth_data[23]),
                toFloat(arr_aeth_data[25]),
                0,
                0,
                0,
                0,
                round(toFloat(arr_aeth_data[22])*1000,4),
                round(toFloat(arr_aeth_data[22])*1000,5),
                toFloat(arr_aeth_data[51]),
            ]
        else:
            #so program still receives an expected array of numbers
            return [0]
    except UnicodeDecodeError:
        received_data = (received_data+ aeth_ser.read(data_left))
        print(received_data)
        return [0]
    
#initialize all three ports as global variables, keep open until end of labview program
def openPorts(COMport1, COMport2, aeth_port):
    global flow_controller_1
    flow_controller_1 = FlowController(port=COMport1)
    global flow_controller_2
    flow_controller_2 = FlowController(port=COMport2)
    global aeth_ser
    aeth_ser = serial.Serial(aeth_port,115200,timeout=0.1)

#close all three ports to avoid future errors
def closePorts():
    flow_controller_1.close()
    flow_controller_2.close()
    aeth_ser.close()

#use the alicat library to return an array of data from either mass flow controller and set the setpoint
def getMFCData(number):

    #takes the absolute value of flow because otherwise LabVIEW will raise an error
    if number ==1:
        #flow_controller_1.set_flow_rate(setpoint)
        dictData = flow_controller_1.get()
        arrData = [
            dictData["pressure"],
            dictData["temperature"],
            abs(dictData["volumetric_flow"]),
            abs(dictData["mass_flow"]),
            dictData["setpoint"]
            
        ]
    elif number ==2:
        #flow_controller_2.set_flow_rate(setpoint)
        dictData = flow_controller_2.get()
        arrData = [
            dictData["pressure"],
            dictData["temperature"],
            abs(dictData["volumetric_flow"]),
            abs(dictData["mass_flow"]),
            dictData["setpoint"]
            
        ]
    return(arrData)

def setSetPoint(number,setpoint):
    if (number == 1):
        flow_controller_1.set_flow_rate(setpoint)
    elif (number == 2):
        flow_controller_2.set_flow_rate(setpoint)
        
def testFlowData(flowPort):
    global flow_controller_1
    flow_controller_1 = FlowController(port=flowPort)
    for i in range(10):
        print(flow_controller_1.get())
        sleep(0.5)
    flow_controller_1.close()

def openFlowPort(flowPort):
    global flow_controller_1
    flow_controller_1 = FlowController(port=flowPort)

def getFlowData():
    return flow_controller_1.get()

def closeFlowPort():
    flow_controller_1.close()

def openAethPort(aeth_port,baudrate):
    global aeth_ser
    aeth_ser = serial.Serial(aeth_port,baudrate,timeout=0.1)
    
def closeAethPort():
    aeth_ser.close()

def startSerial(portName):
    global ser
    ser = serial.Serial(
        port = portName,
        baudrate = 115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0.7
    )

def sendSerial(message):
    ser.write(message.encode())

def endSerial():
    ser.close()

def testSerial():
    startSerial()
    for i in range(10):
        sendSerial("1open0.5")
        time.sleep(1)
    endSerial()

#check that a port exists
def checkPort(COMport):
    return os.path.exists(COMport)

#Exponentially weighted mean
def ewm(array, comNumber):
    df = pd.DataFrame({'Bc':array})

    #gets the EWM dataframe of the panda dataframe
    meanie = df.ewm(com=comNumber).mean()
    last = len(array)-1
    return(meanie['Bc'][last])    

def testPAXConnection(PAXport):
    openAethPort(PAXport,115200)
    real = False
    startTime = time.time()
    while time.time() - startTime < 2:
        data = getMicroAethData()
        real = real or data != [0]
        print(data)
    closeAethPort()
    if real:
        return "PAX connection functional"
    else:
        return "PAX connection failed. Check RS232 cord."

def testMFCConnection(port1, port2):
    try:
        global flow_controller_1
        flow_controller_1 = FlowController(port=port1)
        global flow_controller_2
        flow_controller_2 = FlowController(port=port2)
    except Exception as e:
        flow_controller_1.close()
        flow_controller_2.close()
        return "Access denied to flow controller serial ports. Check for programs currently using them."
    try:
        data = flow_controller_1.get()
    except Exception as e:
        print(e)
        flow_controller_1.close()
        flow_controller_2.close()
        return "Check cable connection to flow controller 1, and ensure the flow controller is powered on."
    try:
        data = flow_controller_2.get()
    except Exception as e:
        print(e)
        flow_controller_1.close()
        flow_controller_2.close()
        return "Check cable connection to flow controller 2, and ensure the flow controller is powered on."
    flow_controller_1.close()
    flow_controller_2.close()
    return "Flow controller communication functional :) "


def testSerialConnection(raspberryPort):
    try:
        startSerial(raspberryPort)
    except Exception as e:
        print(e)
        return "Check if USB to UART bridge is plugged in"

    sendSerial("testing")
    received_data = ser.read()
    sleep(0.04)
    
    #number of bytes left in the bffer
    data_left = ser.inWaiting()
    
    #add left over bytes and decode into a string
    received_data = (received_data+ ser.read(data_left)).decode()
    if received_data == "communication confirmed":
        ser.close()
        return "raspberry pi serial communication functional"
    else:
        ser.close()
        return "check that raspberry pi is on and running"
    ser.close()
    
def testSolenoid(raspberryPort):
    startSerial(raspberryPort)
    print("listen for the solenoid pinch valve")
    time.sleep(1)
    sendSerial("1open1.0")
    check = input("Hear the solenoid pulse? (y/n)")
    if check.lower() == "y" or check.lower() == "yes":
        ser.close()
        return "solenoid communcation functional"
    else:
        print("watch the relay light")
        time.sleep(1)
        sendSerial("1open1.0")
        relay = input("Did you see it turn on? (y/n)")
        ser.close()
        if relay.lower() == "y" or relay.lower() == "yes":
            return "check wiring from relay to solenoid and power supply"
        else:
            return "check wiring from relay to pi"

def testBallValves(raspberryPort):
    startSerial(raspberryPort)
    print("listen for the ball valves")
    time.sleep(1)
    sendSerial("soot")
    time.sleep(5)
    sendSerial("air")
    time.sleep(2)
    check = input("Hear the ball valves move? (y/n)")
    if check.lower() == "y" or check.lower() == "yes":
        ser.close()
        return "ball valve communcation functional"
    else:
        print("watch the relay light")
        time.sleep(1)
        sendSerial("soot")
        time.sleep(5)
        sendSerial("air")
        time.sleep(2)
        relay = input("Did you see it turn on? (y/n)")
        ser.close()
        if relay.lower() == "y" or relay.lower() == "yes":
            return "check wiring from relay to ball valves and power supply"
        else:
            return "check wiring from relay to pi"

def testAirFlow(port1):
    global flow_controller_1
    flow_controller_1 = FlowController(port=port1)
    setSetPoint(1, 7.0)
    time.sleep(2)
    flow = flow_controller_1.get()["mass_flow"]
    setSetPoint(1,0.0)
    flow_controller_1.close()
    if flow > 6.8:
        return "air compressor connection functional"
    if flow < 1:
        return "Check air compressor connection"
    else:
        return "Check air compressor pressure setting"

def testPropaneFlow(port2):
    global flow_controller_2
    flow_controller_2 = FlowController(port=port2)
    setSetPoint(2, 0.03)
    time.sleep(4)
    flow = flow_controller_2.get()["mass_flow"]
    setSetPoint(2,0.0)
    flow_controller_2.close()
    if flow > 0.025:
        return "propane connection functional"
    if flow < 0.01:
        return "Check propane connection"
    else:
        return "Check propane regulator setting"

def debugloop(function):
    while True:
        time.sleep(1)
        x = function
        print(x)
        if "functional" in x:
            break

def debuggingSetup(port1, port2, PAXport, raspberryPort):
     debugloop(testPAXConnection(PAXport))
     debugloop(testMFCConnection(port1,port2))
     debugloop(testSerialConnection(raspberryPort))
     debugloop(testSolenoid(raspberryPort))
     debugloop(testBallValves(raspberryPort))
     debugloop(testAirFlow(port1))
     debugloop(testPropaneFlow(port2))
