import serial
import alicat
import os
import socket
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

#start tcp socket to send data to the raspberry pi
def startTCP():
    #creates global client socket variable
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #create a second socket for receiving flame sensor data from the rasberry pi
    global recv_socket
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_socket.bind(('0.0.0.0',3401))
    recv_socket.setblocking(0)
    recv_socket.settimeout(0.2)

    #set socket to raspberry pi's ip address at a common port
    ip = '192.168.7.163'
    port = 3400

    #global socket address to use in other functions
    global address
    address = (ip,port)

#send data over tcp socket
def sendTCP(message):
    client_socket.sendto(message.encode(), address)

#end tcp socket at the end of the LabVIEW program to avoid future errors
def endTCP():
    sendTCP("end")
    client_socket.close()
    recv_socket.close()

#test tcp sending socket
def testTCP():
    startTCP()
    for i in range(1,20):
        print("testing")
        sendTCP("testing: " + str(i))
        sleep(0.5)
    endTCP()

#send a request for data to the raspberry pi and then try to decode received data
def flameTCP(num):
    sendTCP("flame" + str(num))
    try:
        flame_data, ad = recv_socket.recvfrom(16)
        return(int(flame_data.decode()))
    except Exception as e:
        return(1)
    
#micro aeth serial testing
def testAeth():
    openAethPort("COM5")
    i = 0
    while i<10:
        x = getMicroAethData()
        i+=1
        sleep(1)
        print(x)
    closeAethPort()
    
#get MA350 data and export an array of necessary values to LabVIEW
def getMicroAethData():
    #read first byte
    received_data = aeth_ser.read()
    sleep(0.01)

    #number of bytes left in the bffer
    data_left = aeth_ser.inWaiting()

    #add left over bytes and decode into a string
    received_data = (received_data+ aeth_ser.read(data_left)).decode()

    #split the received data into na array
    arr_aeth_data = received_data.split(',')

    #check that the serial data is actually the MA350 data we want
    if arr_aeth_data[0][0:5] == "MA350" and len(arr_aeth_data) >= 50:
        #timebase, tape position, flow setpoint, flow total, sample temp, sample rh, sample dewpoit, uv atn1, uv atn2, ir atn1, ir atn2, ir bc1, ir bcc
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
            toFloat(arr_aeth_data[71])
        ]
    else:
        #so LabVIEW still receives an expected array of numbers
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
    
def openAethPort(aeth_port):
    global aeth_ser
    aeth_ser = serial.Serial(aeth_port,115200,timeout=0.1)
    
def closeAethPort():
    aeth_ser.close()

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

#test that mfc data is being read
def testMFC():
    openPort("COM3","COM4","COM5")
    for i in range(1,20):
        print(getMFCData(0,2))
        sleep(0.5)
    closePorts()




