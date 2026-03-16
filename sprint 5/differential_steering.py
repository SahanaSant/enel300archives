

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
):
    """Convert joystick x/y values (0..65535) into differential pivot commands.

    Returns:
        (left_dir, left_speed, right_dir, right_speed)
    """
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
