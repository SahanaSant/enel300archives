import utime
from slave_bluetooth import uart, parse_bt_message, decode_direction
from differential_steering import apply_joystick_pivot


if __name__ == "__main__":
    last_dir = "C"
    last_x = 0
    last_y = 0
    bt_status = "Waiting BT"

    while True:
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
                        # Stop motors on press while testing steering.
                        apply_joystick_pivot(
                            0, 0,
                            pwm_min_run=20,
                            pwm_max=60,
                            pivot_threshold=0.15,
                            low_edge=600,
                            high_edge=60000,
                        )
                        bt_status = "PRESS"
                        uart.write("ok,press\n")

                    elif msg_type == "xy":
                        last_x = x_val
                        last_y = y_val
                        last_dir = decode_direction(x_val, y_val)

                        left_dir, left_spd, right_dir, right_spd = apply_joystick_pivot(
                            x_val, y_val,
                            pwm_min_run=20,
                            pwm_max=60,
                            pivot_threshold=0.15,
                            low_edge=600,
                            high_edge=60000,
                        )

                        bt_status = "OK"
                        uart.write("ok,{},{}\n".format(x_val, y_val))

                        print(
                            "STEER:", "{},{},{},{}".format(
                                left_dir, left_spd, right_dir, right_spd
                            )
                        )

                    else:
                        bt_status = "BAD"
                        uart.write("err,bad_packet\n")

                    print(
                        "RX:", incoming,
                        "| DIR:", last_dir,
                        "| X,Y:", "{},{}".format(last_x, last_y),
                        "| BT:", bt_status
                    )

        utime.sleep_ms(10)
