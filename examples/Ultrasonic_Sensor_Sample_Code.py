from hcsr04 import HCSR04 # Must have this library saved on Pico to work
from time import sleep

# Initialize sensor with trigger and echo pins
sensor = HCSR04(trigger_pin=21, echo_pin=20)

while True:
    try:
        distance = sensor.distance_cm()
        print('Distance:', distance, 'cm')
        sleep(0.1) # sensor doesn't work well without delay
    except OSError as ex:
        print('ERROR getting distance:', ex)
        break
