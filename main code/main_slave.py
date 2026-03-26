from machine import Pin, PWM, ADC, UART, I2C
from time import sleep
from hcsr04_pi import HCSR04 # Must have this library saved on Pico to work
from pico_i2c_lcd import I2cLcd
import time


uart = UART(0,baudrate=9600, tx =Pin(16), rx=Pin(17))

act = ""

# === L298N Motor Driver ===
# Motor A
motor_a_in1 = Pin(28, Pin.OUT)
motor_a_in2 = Pin(27, Pin.OUT)
motor_a_en = PWM(Pin(26))
motor_a_en.freq(1000)
motor_a_correction = 1.0 # Adjust so both motors have same speed

# Motor B
motor_b_in3 = Pin(13, Pin.OUT)
motor_b_in4 = Pin(14, Pin.OUT)
motor_b_en = PWM(Pin(15))
motor_b_en.freq(1000)
motor_b_correction = 1.0 # Adjust so both motors have same speed

# === Ultrasonic Sensor ===
trig = Pin(18, Pin.OUT) #Can modify these pin numbers
echo = Pin(20, Pin.IN)

# === LED Light ===
led = Pin(4, Pin.OUT)

def get_distance(): #For Ultrasonic Sensor
    trig.low()
    time.sleep_us(2)
    
    trig.high()
    time.sleep_us(10)
    trig.low()

    while echo.value() == 0:
        start = time.ticks_us()
    
    while echo.value() == 1:
        end = time.ticks_us()

    duration = time.ticks_diff(end, start)
    distance = (duration * 0.0343) / 2
    return distance


# Function to control Motor A
def motor_a(direction = "stop", speed = 0):
    adjusted_speed = int(speed * motor_a_correction)  # Apply correction
    if direction == "forward":
        motor_a_in1.value(0)
        motor_a_in2.value(1)
    elif direction == "backward":
        motor_a_in1.value(1)
        motor_a_in2.value(0)
    else:  # Stop
        motor_a_in1.value(0)
        motor_a_in2.value(0)
    motor_a_en.duty_u16(int(adjusted_speed * 65535 / 100))  # Speed: 0-100%

# Function to control Motor B
def motor_b(direction = "stop", speed = 0):
    adjusted_speed = int(speed * motor_b_correction)  # Apply correction
    if direction == "forward":
        motor_b_in3.value(1)
        motor_b_in4.value(0)
    elif direction == "backward":
        motor_b_in3.value(0)
        motor_b_in4.value(1)
    else:  # Stop
        motor_b_in3.value(0)
        motor_b_in4.value(0)
    motor_b_en.duty_u16(int(adjusted_speed * 65535 / 100))  # Speed: 0-100%


while True:
    
    if uart.any():
        data = uart.readline()
        print("Slave recived", data.decode('utf-8').strip())
        com = data.decode('utf-8').strip()
        
        if (com == "left"):
            motor_a("backward", 38)
            motor_b("forward", 40)
            sleep(0.2)
            motor_a()
            motor_b()
    
    
        elif (com == "right"):
            print("slave responding, Pong")
            motor_a("forward", 38)
            motor_b("backward", 40)
            sleep(0.2)
            motor_a()
            motor_b()
            
    
    
        elif (com == "up"):
            print("slave responding, Pong")
            motor_a("forward", 38)
            motor_b("forward", 40)
            sleep(1)
            motor_a()
            motor_b()
       
    
        elif (com == "down"):
            print("slave responding, Pong")
            motor_a("backward", 38)
            motor_b("backward", 40)
            sleep(1)
            motor_a()
            motor_b()
        
        if (com == "press"):
            print("slave responding, Pong")
            sleep(1)
            uart.write(f"{com}\n")
            
        
        else:
            print("fail motors")
            sleep(1)
            uart.write("fail motors\n")
    
    #Send readings of course when the joystick and car are paired.
    output = get_distance()
    print(output)
    utime.sleep(0.1)
    
    act = "{output:.2f}"
    print (f'{act}\n')
    print("slave about to send distance")
    uart.write(act)
    time.sleep (0.5)
    
    if uart.any():
        data = uart.readline()
        print("Slave recieved distance check", data.decode('utf-8').strip())
    
    print("---")

    sleep(0.1)
#     
#     # Travel forward
#     motor_a("forward", 38)
#     motor_b("forward", 40)
#     sleep(2.6)
#     motor_a()
#     motor_b()
#     
#     # Travel backward
#     motor_a("backward", 38)
#     motor_b("backward", 40)
#     sleep(2.6)
#     motor_a()
#     motor_b()
