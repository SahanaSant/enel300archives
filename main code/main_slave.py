from machine import Pin, PWM, ADC, UART, I2C
import time
from hcsr04_pi import HCSR04 # Must have this library saved on Pico to work

# === Bluetooth Module ===
uart = UART(0,baudrate=9600, tx =Pin(16), rx=Pin(17))

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
trig = Pin(12, Pin.OUT) #Can modify these pin numbers
echo = Pin(11, Pin.IN)

# === LED Pinmapping ===
led = Pin(10, Pin.OUT)

def get_distance(): #For Ultrasonic Sensor
    trig.low()
    #time.sleep(1)
    
    trig.high()
    #time.sleep(1)
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
            time.sleep(1)
            motor_a()
            motor_b()
    
    
        elif (com == "right"):
            print("slave responding, Pong")
            motor_a("forward", 38)
            motor_b("backward", 40)
            time.sleep(1)
            motor_a()
            motor_b()
            
    
    
        elif (com == "up"):
            print("slave responding, Pong")
            motor_a("forward", 38)
            motor_b("forward", 40)
            time.sleep(1)
            motor_a()
            motor_b()
       
    
        elif (com == "down"):
            print("slave responding, Pong")
            motor_a("backward", 38)
            motor_b("backward", 40)
            time.sleep(1)
            motor_a()
            motor_b()
        
        elif (com == "press"):
            print("pass")
            led.value(1)
            time.sleep(1)
            print("slave responding, Pong")
            uart.write(f"{com}\n")
            led.value(0)
            
        
        else:
            print("fail")
            time.sleep(0.1)
            uart.write("fail\n")
        
    output = get_distance()
    uart.write(f"{output:.2f}\n")
    #utime.sleep(0.1)
    
    time.sleep(0.1)
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