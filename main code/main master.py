import utime
from master_bluetooth import xm, ym, button, uart2, LOW_EDGE, HIGH_EDGE

SEND_PERIOD_MS = 120


def build_steering_payload(x_val, y_val, button_val):
    """Build steering-only packet: 'press' or numeric 'x,y'."""
    if button_val == 0:
        return "press", "PRESS"

    x_active = (x_val <= LOW_EDGE) or (x_val >= HIGH_EDGE)
    y_active = (y_val <= LOW_EDGE) or (y_val >= HIGH_EDGE)

    tx_x = x_val if x_active else 0
    tx_y = y_val if y_active else 0

    x_dir = "L" if x_val <= LOW_EDGE else ("R" if x_val >= HIGH_EDGE else "")
    y_dir = "U" if y_val <= LOW_EDGE else ("D" if y_val >= HIGH_EDGE else "")

    if x_dir and y_dir:
        direction = "{}+{}".format(x_dir, y_dir)
    else:
        direction = x_dir or y_dir or "C"

    return "{},{}".format(tx_x, tx_y), direction


if __name__ == "__main__":
    last_send_ms = utime.ticks_ms()

    while True:
        now = utime.ticks_ms()

        if utime.ticks_diff(now, last_send_ms) >= SEND_PERIOD_MS:
            last_send_ms = now

            x_val = xm.read_u16()
            y_val = ym.read_u16()
            button_val = button.value()

            payload, direction = build_steering_payload(x_val, y_val, button_val)
            uart2.write(payload + "\n")

            print(
                "TX:", payload,
                "| XY:", "{},{}".format(x_val, y_val),
                "| DIR:", direction,
            )

            if uart2.any():
                reply = uart2.readline()
                if reply:
                    try:
                        print("RX:", reply.decode("utf-8").strip())
                    except Exception:
                        print("RX: <decode error>")

        utime.sleep_ms(10)
