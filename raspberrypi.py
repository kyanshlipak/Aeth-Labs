import serial
from gpiozero import LED
import time
import datetime

#initialize valve at pins 12 and 16
valve1Power = LED(16)
valve1 = LED(12)
valve1Power.on()

ser = serial.Serial(
    port = '/dev/ttyS0',
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 0.05
)

#open or close either valve based on the incoming tcp message
def valve(message):
    if message.startswith("1open"):
        try:
            sleepInterval = float(message.replace("1open",'',1))
            startTime = time.time()
            valve1.on()
            time.sleep(sleepInterval)
            print(str(datetime.datetime.now())+ ": " + str(round(time.time()-startTime,6)))
            valve1.off()
        except ValueError:
           pass
    elif message == "end":
        ser.close()
        GPIO.cleanup()
        print(message)
        
def receive_data():    
    #receive data
    try:
        x = ser.readline().decode()
    except UnicodeDecodeError:
        x = ''
    if len(x.split()) > 0:
        print(x)
        valve(x)
        ser.flushInput()
        
    
def manualPulse(pulseTime):
    print("1 on")
    startTime = time.time()
    valve1.on()
    time.sleep(pulseTime)
    print("1 off: " + str(round(time.time()-startTime,6)))
    valve1.off()

def pulsing(on,off,totalTime):
    startTime = time.time()
    i = 0
    while time.time() - startTime < totalTime:
        p = time.time()
        print("--- 1 on")
        x = on - on * (i*0.001)
        valve1.on()
        time.sleep(x)
        print("1 off: " + str(round(time.time()-p,6)))
        valve1.off()
        for i in range(1,6):
            time.sleep(off/5)
            print(str(int(off/5)*i))
        i+=1

manualPulse(0.1)
while True:
    receive_data()

#pulsing(2,30,90)
#time.sleep(600)
#manualPulse(1)          
#pulsing(5,20,50)
#time.sleep(30)
#pulsing(1,30,1200)
#time.sleep(1200)

#pulsing(3,20,50)
#time.sleep(30)
#pulsing(1,50,1200)
#time.sleep(1200)

#pulsing(1.3,20,50)
#time.sleep(30)
#pulsing(1,100,1200)
#time.sleep(1200)
        
#manualPulse(1)
#pulsing(0.5,100,1200)
