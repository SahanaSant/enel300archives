from machine import Pin, PWM, ADC, UART, I2C
from time import sleep, ticks_us, ticks_diff
import utime
from hcsr04_pi import HCSR04 # Must have this library saved on Pico to work

led = Pin(10, Pin.OUT)
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
d_sensor = HCSR04(trigger_pin=12, echo_pin=11)


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
    
def get_distance(): #For Ultrasonic Sensor
    
    
    return d_sensor.distance_cm()

def drive_from_command(com, speed=50):
    if com == "left":
        motor_a("backward", speed)
        motor_b("forward", speed)
    elif com == "right":
        motor_a("forward", speed)
        motor_b("backward", speed)
    elif com == "up":
        motor_a("forward", speed)
        motor_b("forward", speed)
    elif com == "down":
        motor_a("backward", speed)
        motor_b("backward", speed)
    elif com == "stop":
        motor_a()
        motor_b()
    else:
        return False
    return True

while True:
    
    if uart.any():
        data = uart.readline()
        if not data:
            #sleep(0.02)
            continue

        com = data.decode('utf-8').strip()
        print("Slave recived", com)

        if com in ("left", "right", "up", "down", "stop"):
            drive_from_command(com, 50)

        elif com == "press":
            led.value(1)
            output = get_distance()
            led.value(0)
            print(f'{output}\n')
            uart.write(f"{output:.2f}\n")

        else:
            print("fail")
    #Car battery works fine until calling getting output 
    
            
    sleep(0.02)
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




