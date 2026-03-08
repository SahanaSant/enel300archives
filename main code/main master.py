import utime
from master_bluetooth import (
    xm,
    ym,
    button,
    uart2,
    LOW_EDGE,
    HIGH_EDGE,
    build_bt_payload,
    send_bt_payload,
)

SEND_PERIOD_MS = 120


def decode_direction_for_debug(x_val, y_val, button_val):
    """Return a human-readable joystick direction string for logging."""
    if button_val == 0:
        return "PRESS"

    x_dir = ""
    y_dir = ""

    if x_val <= LOW_EDGE:
        x_dir = "L"
    elif x_val >= HIGH_EDGE:
        x_dir = "R"

    if y_val <= LOW_EDGE:
        y_dir = "U"
    elif y_val >= HIGH_EDGE:
        y_dir = "D"

    if x_dir and y_dir:
        return "{}+{}".format(x_dir, y_dir)
    return x_dir or y_dir or "C"


if __name__ == "__main__":
    last_send_ms = utime.ticks_ms()

    while True:
        now = utime.ticks_ms()

        if utime.ticks_diff(now, last_send_ms) >= SEND_PERIOD_MS:
            last_send_ms = now

            x_val = xm.read_u16()
            y_val = ym.read_u16()
            button_val = button.value()

            payload = build_bt_payload(x_val, y_val, button_val)
            send_bt_payload(payload)

            print(
                "TX:", payload,
                "| XY:", "{},{}".format(x_val, y_val),
                "| DIR:", decode_direction_for_debug(x_val, y_val, button_val),
            )

            if uart2.any():
                reply = uart2.readline()
                if reply:
                    try:
                        print("RX:", reply.decode("utf-8").strip())
                    except Exception:
                        print("RX: <decode error>")

        utime.sleep_ms(10)
