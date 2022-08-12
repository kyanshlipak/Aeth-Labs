import serial
import time
def openAethPort(aeth_port,baudrate):
    global aeth_ser
    aeth_ser = serial.Serial(aeth_port,baudrate,timeout=0.000001)

def closePort():
    try: aeth_ser.close()
    except Exceptions: pass

#micro aeth serial testing
def testAeth():
    openAethPort("COM6", 500000)
    i = 0
    while i<20:
        x = getMicroAethData()
        i+=1
        sleep(1)
        print(x)

    closeAethPort()
    
#get MA350 data and export an array of necessary values to LabVIEW
def getMicroAethData():
    #read first byte

    received_data = aeth_ser.read()
    sleep(0.04)

    #number of bytes left in the bffer
    data_left = aeth_ser.inWaiting()
    
    #add left over bytes and decode into a string
    received_data = (received_data+ aeth_ser.read(data_left)).decode()

    #split the received data into na array
    arr_aeth_data = received_data.split(',')

def hexStringToInt(byte):
    return int.from_bytes(byte,"big")

def hexDate(bytes3):
    year = bytes3[0] + 2000
    month  = bytes3[1]
    day = bytes3[2]
    if len(bytes3) > 3:
        dayOfWeek = bytes3[3]
    datestring = str(year) + '/' + str(month) + '/' + str(day)
    return(datestring)

def addZero(num):
    if num<10:
        time = '0'+str(num)
    else:
        time = str(num)
    return time

def hexTime(bytes3):
    hours = bytes3[0]
    minutes = bytes3[1]
    seconds = bytes3[2]
    
    timestring = addZero(hours) + ':' + addZero(minutes) + ':' + addZero(seconds)
    return timestring

def hexFlow(bytes1):
    flow = bytes1*25
    return str(flow) + 'mlpm'

def hexFlow2(bytes2):
    return int.from_bytes(bytes2,"little")

def hexPCBTemp(bytes1):
    return str(bytes1) + 'C'

def hexReference(bytes3):
    num = int.from_bytes(bytes3,"little")
    return(num)

def hexStatus(bytes1):
    return str(bytes1)

def hexBattery(bytes2):
    battery = int.from_bytes(bytes2,'little')
    return str(battery) + "%"

def streamToDict(stream):
    if stream[2:8] == b'AE5X:M':
        print(stream)
        print("length: ",len(stream[8:-1]))
        stream = stream[8:-1]
        streamDict = {
            'reference':hexReference(stream[0:3]),
            'sensor 1':hexReference(stream[3:6]),
            'feedback':hexReference(stream[6:9]),
            'flow': hexFlow2(stream[9:11]),
            'PCB temp':hexPCBTemp(stream[11]),
            'date': hexDate(stream[12:15]),
            'time': hexTime(stream[15:18]),
            'status':hexStatus(stream[18]),
            'battery':hexBattery(stream[19:21]),
            'CRC':stream[-1]
        }
        print(streamDict)
    else:
        print(stream)

def getCheckSum(data):
    length = len(data)
    checksum = length ^ data[0]
    for byte in data[1:]:
        checksum = checksum ^ byte
    return checksum

def write(data):
    checkSum = getCheckSum(data).to_bytes(1,'big')
    length = len(data).to_bytes(1,'big')
    message = b"\x02" +length+ data + checkSum + b"\x03"
    aeth_ser.write(message)

def getResponse():
    while True:
        data = aeth_ser.read()
        time.sleep(0.1)
        data_left = aeth_ser.inWaiting()
        received_data = (data+ aeth_ser.read(data_left))
        if len(received_data)>0:
            print(received_data)
            return(received_data)
          
#openAethPort("COM6", 500000)

def getDate():
    write(b"AE5X:D")
    reply = getResponse()
    if reply [2:8] == b"AE5X:D":
        return hexDate(reply[8:11])
    

