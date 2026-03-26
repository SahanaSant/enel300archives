from machine import Pin, ADC, UART, I2C
import utime
import time
from pico_i2c_lcd import I2cLcd

uart2 = UART(1,baudrate=9600, tx =Pin(8), rx=Pin(9))

xm= ADC(Pin(26))
ym= ADC(Pin(27))
button = Pin(22,Pin.IN, Pin.PULL_UP)

#LCD display
#i2c = I2C(0, sda=Pin(0), scl=Pin(1)) #Can modify these pin numbers
#lcd = I2cLcd(i2c, 0x27, 2, 16)

#lcd.clear()   # <-- put it here (only once)

"""
slave_add = "2025,08,004BEC"

def send_at(command):
    uart.write(command + '\r\n')
    time.sleep(0.1)
    if uart.any():
        print(uart.read().decode('utf-8'))
        
def send_at2(command):
    uart2.write(command + '\r\n')
    time.sleep(0.1)
    if uart2.any():
        print(uart2.read().decode('utf-8'))
        
print("Config Sla")
send_at('AT+ORGL')
send_at('AT+ROLE=0')
send_at('AT+ADDR?')
print("Done")

print("config mas")
send_at2('AT+ORGL')
send_at2('AT+ROLE=1')
send_at2('AT+CMODE=0')
send_at2('AT+BIND=' + slave_add)
print("mas done")


"""
#Test Code

while True:
    
    xVal  = xm.read_u16()
    yVal = ym.read_u16()
    buttonVal = button.value()
    
    act = ""
    
    if xVal <=600:
        act = ("left")
    elif xVal >=60000:
        act = ("right")
    elif yVal <=600:
        act = ("up")
    elif yVal >=60000:
        act = ("down")
    utime.sleep(0.1)
    
    print("master ping")
    print(f"{act}\n")
    uart2.write(f"{act}\n")
    time.sleep(0.5)
    
    if uart2.any():
        data = uart2.readline()
        print("Master recived", data.decode('utf-8').strip())
        
    print("---")
    
    #Ultrasonic sensor pairing
    if uart2.any():
        data = uart2.readline()
        print("Master recieved distance", data.decode('utf-8').strip())
        com = data.decode('utf-8').strip()
        
        #if (com.isdigit()):
            #print("Master abt to print distance")
            
            #lcd.move_to(0, 0)
            #lcd.putstr("Distance (cm)")
            
            #lcd.move_to(0, 1)
            #lcd.putstr(com)
            
    time.sleep(0.5)

