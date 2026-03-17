from machine import Pin, ADC, UART
import utime
import time

# Master Pico -> HC-05 on UART1 (change pins if needed)
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

x_axis = ADC(Pin(26))
y_axis = ADC(Pin(27))
button = Pin(22, Pin.IN, Pin.PULL_UP)

LOW_EDGE = 600
HIGH_EDGE = 60000


def send_at(command):
    """Optional AT helper for configuring HC-05 as master."""
    uart.write(command + "\r\n")
    time.sleep(0.1)
    if uart.any():
        try:
            print(uart.read().decode("utf-8"))
        except Exception:
            pass


def build_command():
    x_val = x_axis.read_u16()
    y_val = y_axis.read_u16()
    button_val = button.value()

    x_dir = ""
    y_dir = ""

    if x_val <= LOW_EDGE:
        x_dir = "left"
    elif x_val >= HIGH_EDGE:
        x_dir = "right"

    if y_val <= LOW_EDGE:
        y_dir = "up"
    elif y_val >= HIGH_EDGE:
        y_dir = "down"

    if button_val == 0:
        act = "press"
        direction = "press"
    elif x_dir and y_dir:
        act = "{},{}".format(x_val, y_val)
        direction = "{}+{}".format(x_dir, y_dir)
    elif x_dir:
        act = "{},0".format(x_val)
        direction = x_dir
    elif y_dir:
        act = "0,{}".format(y_val)
        direction = y_dir
    else:
        act = "0,0"
        direction = "center"

    return act, x_val, y_val, direction


def send_line(payload):
    uart.write(payload + "\n")


def read_line():
    if not uart.any():
        return None
    data = uart.readline()
    if not data:
        return None
    try:
        return data.decode("utf-8").strip()
    except Exception:
        return None


while True:
    act, x_val, y_val, direction = build_command()
    send_line(act)
    rx = read_line()

    print(
        "TX:", act,
        "| XY:", "{},{}".format(x_val, y_val),
        "| DIR:", direction,
        "| RX:", rx if rx else "-"
    )

    utime.sleep_ms(120)
