from machine import Pin, UART
import utime
import time

# Slave Pico -> HC-05 on UART1 (change pins if needed)
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

LOW_EDGE = 600
HIGH_EDGE = 60000


def send_at(command):
    """Optional AT helper for configuring HC-05 as slave."""
    uart.write(command + "\r\n")
    time.sleep(0.1)
    if uart.any():
        try:
            print(uart.read().decode("utf-8"))
        except Exception:
            pass


def parse_message(msg):
    if msg in ("press", "pressed"):
        return "press", None, None

    parts = msg.split(",")
    if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
        x_val, y_val = map(int, parts)
        return "xy", x_val, y_val

    return "bad", None, None


def decode_direction(x_val, y_val):
    x_dir = "L" if x_val <= LOW_EDGE else ("R" if x_val >= HIGH_EDGE else "")
    y_dir = "U" if y_val <= LOW_EDGE else ("D" if y_val >= HIGH_EDGE else "")
    if x_dir and y_dir:
        return "{}+{}".format(x_dir, y_dir)
    return x_dir or y_dir or "C"


def send_line(payload):
    uart.write(payload + "\n")


while True:
    if uart.any():
        data = uart.readline()
        if data:
            try:
                incoming = data.decode("utf-8").strip()
            except Exception:
                incoming = ""

            if not incoming:
                utime.sleep_ms(10)
                continue

            msg_type, x_val, y_val = parse_message(incoming)

            if msg_type == "press":
                reply = "ok,press"
                direction = "PRESS"
            elif msg_type == "xy":
                direction = decode_direction(x_val, y_val)
                reply = "ok,{},{}".format(x_val, y_val)
            else:
                direction = "BAD"
                reply = "err,bad_packet"

            send_line(reply)
            print(
                "RX:", incoming,
                "| DIR:", direction,
                "| TX:", reply
            )

    utime.sleep_ms(10)
