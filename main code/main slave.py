import utime
from LCDdisplay import *
from slave_bluetooth import *
from master_bluetooth import *


# This file now assumes imports provide:
# uart, write_lcd, measure_distance_once_cm, DISPLAY_SMOOTH_ALPHA,
# parse_bt_message, decode_direction

SENSOR_PERIOD_MS = 120
LCD_PERIOD_MS = 180


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
