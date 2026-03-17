

from motor_module import motor_a, motor_b


def clamp(value, low, high):
    return max(low, min(high, value))


def _to_signed_unit(raw, center, deadzone):
    """Map raw joystick ADC value to -1.0..1.0 with center deadzone."""
    if raw >= center:
        span = max(1, 65535 - center)
        norm = (raw - center) / span
    else:
        span = max(1, center)
        norm = (raw - center) / span

    if abs(norm) < deadzone:
        return 0.0
    return clamp(norm, -1.0, 1.0)


def _command_from_signed(cmd, pwm_min_run, pwm_max):
    """Convert signed command (-1..1) into (direction, speed_percent)."""
    mag = abs(cmd)
    if mag <= 0.0:
        return "stop", 0

    speed = int(round(pwm_min_run + (pwm_max - pwm_min_run) * mag))
    speed = clamp(speed, 0, 100)
    direction = "forward" if cmd > 0 else "backward"
    return direction, speed


def _edge_axis_to_signed(value, low_edge, high_edge):
    """Map ms-code axis format to signed command: left/up=-1, right/down=+1, center=0."""
    if value == 0:
        return 0.0
    if value <= low_edge:
        return -1.0
    if value >= high_edge:
        return 1.0
    return 0.0


def mix_joystick_to_pivot(
    x_val,
    y_val,
    center_x=32768,
    center_y=32768,
    deadzone=0.05,
    pwm_min_run=20,
    pwm_max=100,
    pivot_threshold=0.15,
    invert_y=True,
    input_mode="ms_edges",
    low_edge=600,
    high_edge=60000,
):
    """Convert joystick x/y values into differential pivot commands.

    input_mode:
        - "ms_edges": uses ms-code rules (0=center, <=low_edge, >=high_edge)
        - "raw": uses centered normalization around center_x/center_y

    Returns:
        (left_dir, left_speed, right_dir, right_speed)
    """
    if input_mode == "ms_edges":
        x = _edge_axis_to_signed(x_val, low_edge, high_edge)
        y = _edge_axis_to_signed(y_val, low_edge, high_edge)
    else:
        x = _to_signed_unit(x_val, center_x, deadzone)
        y = _to_signed_unit(y_val, center_y, deadzone)

    if x == 0.0 and y == 0.0:
        return "stop", 0, "stop", 0

    # Many thumbsticks report lower ADC when pushed up.
    if invert_y:
        y = -y

    # Pivot steering: if little forward command, rotate in place.
    if abs(y) < pivot_threshold:
        left_cmd = x
        right_cmd = -x
    else:
        # Differential/arcade mix.
        left_cmd = y + x
        right_cmd = y - x

    peak = max(1.0, abs(left_cmd), abs(right_cmd))
    left_cmd /= peak
    right_cmd /= peak

    left_dir, left_speed = _command_from_signed(left_cmd, pwm_min_run, pwm_max)
    right_dir, right_speed = _command_from_signed(right_cmd, pwm_min_run, pwm_max)
    return left_dir, left_speed, right_dir, right_speed


def apply_joystick_pivot(x_val, y_val, **kwargs):
    """Apply joystick steering directly using motor_a/motor_b drivers."""
    left_dir, left_speed, right_dir, right_speed = mix_joystick_to_pivot(
        x_val, y_val, **kwargs
    )
    motor_a(left_dir, left_speed)
    motor_b(right_dir, right_speed)
    return left_dir, left_speed, right_dir, right_speed


def mix_fixed_speed_turn(
    x_val,
    low_edge=600,
    high_edge=60000,
    cruise_speed=45,
    turn_delta=15,
    drive_direction="forward",
):
    """Use ms-code edge rules: x<=low -> left, x>=high -> right, else center."""
    cruise_speed = clamp(int(cruise_speed), 0, 100)
    turn_delta = clamp(int(turn_delta), 0, 100)

    if cruise_speed == 0:
        return "stop", 0, "stop", 0

    # Match ms code behavior: left/right are only triggered at edge thresholds.
    # x_val == 0 is treated as center/inactive axis.
    if x_val == 0:
        x_dir = "center"
    elif x_val <= low_edge:
        x_dir = "left"
    elif x_val >= high_edge:
        x_dir = "right"
    else:
        x_dir = "center"

    if x_dir == "center":
        left_speed = cruise_speed
        right_speed = cruise_speed
    elif x_dir == "right":
        # Joystick right -> right turn
        left_speed = clamp(cruise_speed + turn_delta, 0, 100)
        right_speed = clamp(cruise_speed - turn_delta, 0, 100)
    else:
        # Joystick left -> left turn
        left_speed = clamp(cruise_speed - turn_delta, 0, 100)
        right_speed = clamp(cruise_speed + turn_delta, 0, 100)

    return drive_direction, left_speed, drive_direction, right_speed


def apply_fixed_speed_turn(x_val, **kwargs):
    """Apply fixed-speed turning directly using motor_a/motor_b drivers."""
    left_dir, left_speed, right_dir, right_speed = mix_fixed_speed_turn(
        x_val, **kwargs
    )
    motor_a(left_dir, left_speed)
    motor_b(right_dir, right_speed)
    return left_dir, left_speed, right_dir, right_speed
