import utime
from machine import I2C, Pin
import sys
from slave_bluetooth import uart, parse_bt_message, decode_direction
from differential_steering import apply_joystick_pivot

if "libraries" not in sys.path:
    sys.path.append("libraries")

from pico_i2c_lcd import I2cLcd
from hcsr04 import HCSR04


#Some constants
SENSOR_PERIOD_MS = 120
LCD_PERIOD_MS = 180
DISPLAY_SMOOTH_ALPHA = 0.25
LCD_COLS = 16

#Ultrasonic sensor
trig = Pin(16, Pin.OUT) #Can modify these pin numbers
echo = Pin(17, Pin.IN)

#LCD display
i2c = I2C(0, sda=Pin(0), scl=Pin(1)) #Can modify these pin numbers
lcd = I2cLcd(i2c, 0x27, 2, 16)
distance_sensor = HCSR04(trigger_pin=16, echo_pin=17)


def _format_lcd_line(text):
    return str(text)[:LCD_COLS].ljust(LCD_COLS)


def write_lcd(line1, line2):
    lcd.move_to(0, 0)
    lcd.putstr(_format_lcd_line(line1))
    lcd.move_to(0, 1)
    lcd.putstr(_format_lcd_line(line2))


def measure_distance_once_cm():
    try:
        cm = distance_sensor.distance_cm()
    except OSError:
        return None
    if cm <= 0 or cm > 400:
        return None
    return cm


if __name__ == "__main__":
    display_distance = None
    last_dir = "C"
    last_x = 0
    last_y = 0
    bt_status = "Waiting BT"

    write_lcd("Distance (cm)", "Starting...")
    utime.sleep_ms(200)

    last_sensor_ms = utime.ticks_ms()
    last_lcd_ms = utime.ticks_ms()

    while True:
        now = utime.ticks_ms()

        if uart.any():
            data = uart.readline()
            if data:
                try:
                    incoming = data.decode("utf-8").strip()
                except Exception:
                    incoming = ""

                if incoming:
                    msg_type, x_val, y_val = parse_bt_message(incoming)

                    if msg_type == "press":
                        bt_status = "PRESS"
                        uart.write("ok,press\n")
                        
                    elif msg_type == "xy":
                        last_x = x_val
                        last_y = y_val
                        last_dir = decode_direction(x_val, y_val)
                        bt_status = "OK"
                        uart.write("ok,{},{}\n".format(x_val, y_val))
                        
                        #Now steering the car 
                        left_dir, left_spd, right_dir, right_spd = apply_joystick_pivot(
                        x_val, y_val,
                        pwm_min_run=20,
                        pwm_max=60,
                        pivot_threshold=0.15,
                        low_edge=600,
                        high_edge=60000,
                        )
                        
                        print("ok,{},{},{},{},{},{}\n".format(
                        x_val, y_val, left_dir, left_spd, right_dir, right_spd
                        ))
                        
                    else:
                        bt_status = "BAD"
                        uart.write("err,bad_packet\n")

                    print(
                        "RX:", incoming,
                        "| DIR:", last_dir,
                        "| X,Y:", "{},{}".format(last_x, last_y),
                        "| BT:", bt_status
                    )

        if utime.ticks_diff(now, last_sensor_ms) >= SENSOR_PERIOD_MS:
            last_sensor_ms = now
            sample = measure_distance_once_cm()
            if sample is not None:
                if display_distance is None:
                    display_distance = sample
                else:
                    display_distance = (
                        DISPLAY_SMOOTH_ALPHA * sample
                        + (1.0 - DISPLAY_SMOOTH_ALPHA) * display_distance
                    )

        if utime.ticks_diff(now, last_lcd_ms) >= LCD_PERIOD_MS:
            last_lcd_ms = now

            if display_distance is None:
                line1 = "Distance: --.-cm"
            else:
                line1 = "D:{:6.2f} cm".format(display_distance)

            line2 = "{} {:05d},{:05d}".format(last_dir, last_x, last_y)
            write_lcd(line1, line2)

        utime.sleep_ms(10)
