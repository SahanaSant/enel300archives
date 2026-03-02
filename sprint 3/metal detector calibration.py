from time import sleep, sleep_ms, sleep_us, ticks_ms, ticks_diff
from machine import Pin, ADC

# --- Hardware Configuration ---
DRIVE_PIN = 16
ADC_PIN = 26
LED_PIN = 25

# --- Pulse/Read Timing ---
PINGS_PER_READING = 40
SAMPLES_PER_PING = 220
DRIVE_PULSE_US = 600
RELEASE_WAIT_US = 1

# --- Startup Calibration ---
CAL_READINGS = 120

# --- Adaptive Noise Model / Thresholds ---
NOISE_ALPHA = 0.02       # How quickly noise estimate adapts
NOISE_MULT = 2.7         # Threshold = noise * NOISE_MULT + NOISE_OFFSET
NOISE_OFFSET = 40
MIN_THRESHOLD = 120
MAX_THRESHOLD = 1200
FORCE_THRESHOLD = 0      # Set >0 to force both thresholds
NOISE_LEARN_NORM = 0.70  # Update noise model only when well below trigger

# --- Detection Gate ---
ARM_NORM = 1.15          # Event strength needed to build toward detect
ARM_COUNT = 2            # Hits needed to detect
RELEASE_NORM = 0.70      # Clear begins below this
RELEASE_COUNT = 5

# --- Baseline Drift Compensation ---
BASELINE_ALPHA_IDLE = 0.001
BASELINE_ALPHA_DETECTED = 0.0005

# --- Startup Settling ---
STARTUP_SETTLE_MS = 3000
SETTLE_BASELINE_ALPHA = 0.01
SETTLE_NOISE_ALPHA = 0.08

PRINT_EVERY_MS = 120

drive = Pin(DRIVE_PIN, Pin.OUT)
adc = ADC(Pin(ADC_PIN))
led = Pin(LED_PIN, Pin.OUT)


def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def percentile(sorted_vals, q):
    """Return percentile q from a non-empty sorted list (q in [0, 1])."""
    idx = int((len(sorted_vals) - 1) * q)
    return sorted_vals[idx]


def compute_threshold(noise_level):
    if FORCE_THRESHOLD > 0:
        return FORCE_THRESHOLD
    raw = int(noise_level * NOISE_MULT + NOISE_OFFSET)
    return clamp(raw, MIN_THRESHOLD, MAX_THRESHOLD)


def measure_one_cycle():
    """Pulse the coil once and capture decay energy."""
    drive.init(Pin.OUT)
    drive.value(1)
    sleep_us(DRIVE_PULSE_US)

    drive.init(Pin.IN)
    sleep_us(RELEASE_WAIT_US)

    total = 0
    for _ in range(SAMPLES_PER_PING):
        total += adc.read_u16()

    drive.init(Pin.OUT)
    drive.value(0)
    return total


def get_stable_reading():
    """Average several pulse measurements to reduce noise."""
    acc = 0
    for _ in range(PINGS_PER_READING):
        acc += measure_one_cycle()
    return acc // PINGS_PER_READING


def calibrate():
    """Build initial baseline and noise estimates from no-metal readings."""
    print("Calibrating... Keep metal away from the coil and keep setup still.")
    led.value(1)
    sleep(1)

    vals = []
    for _ in range(CAL_READINGS):
        vals.append(get_stable_reading())
        sleep_ms(8)

    baseline = sum(vals) / len(vals)

    down_noise = []
    up_noise = []
    for v in vals:
        down = baseline - v
        up = v - baseline
        down_noise.append(down if down > 0 else 0)
        up_noise.append(up if up > 0 else 0)

    down_noise.sort()
    up_noise.sort()

    p95_down = percentile(down_noise, 0.95)
    p95_up = percentile(up_noise, 0.95)
    p99_down = percentile(down_noise, 0.99)
    p99_up = percentile(up_noise, 0.99)

    noise_down = max(1.0, float(p95_down))
    noise_up = max(1.0, float(p95_up))

    t_down = compute_threshold(noise_down)
    t_up = compute_threshold(noise_up)

    led.value(0)
    print("Calibration complete.")
    print(
        "Baseline:", int(baseline),
        "P95Down:", int(p95_down),
        "P95Up:", int(p95_up),
        "P99Down:", int(p99_down),
        "P99Up:", int(p99_up),
        "T_down:", t_down,
        "T_up:", t_up,
    )

    return baseline, noise_down, noise_up


baseline, noise_down, noise_up = calibrate()

detected = False
arm_hits = 0
release_hits = 0
peak_norm = 0.0
boot_ms = ticks_ms()
last_print_ms = ticks_ms()

while True:
    try:
        current_val = get_stable_reading()
        now = ticks_ms()

        if detected:
            baseline += BASELINE_ALPHA_DETECTED * (current_val - baseline)
        else:
            baseline += BASELINE_ALPHA_IDLE * (current_val - baseline)

        down = baseline - current_val
        if down < 0:
            down = 0

        up = current_val - baseline
        if up < 0:
            up = 0

        threshold_down = compute_threshold(noise_down)
        threshold_up = compute_threshold(noise_up)

        norm_down = down / threshold_down
        norm_up = up / threshold_up

        dom_norm = norm_down if norm_down >= norm_up else norm_up

        if dom_norm > peak_norm:
            peak_norm = dom_norm

        settling = ticks_diff(now, boot_ms) < STARTUP_SETTLE_MS
        if settling:
            # Hold detection off during startup and aggressively recenter.
            baseline += SETTLE_BASELINE_ALPHA * (current_val - baseline)
            noise_down = (1.0 - SETTLE_NOISE_ALPHA) * noise_down + SETTLE_NOISE_ALPHA * down
            noise_up = (1.0 - SETTLE_NOISE_ALPHA) * noise_up + SETTLE_NOISE_ALPHA * up
            detected = False
            arm_hits = 0
            release_hits = 0
            led.value(0)
        else:
        # Learn ambient noise only when clearly below trigger region.
            if not detected and arm_hits == 0 and dom_norm < NOISE_LEARN_NORM:
                noise_down = (1.0 - NOISE_ALPHA) * noise_down + NOISE_ALPHA * down
                noise_up = (1.0 - NOISE_ALPHA) * noise_up + NOISE_ALPHA * up

            if not detected:
                # Build arm hits from repeated near/over-threshold events.
                if dom_norm >= 1.40:
                    arm_hits = min(ARM_COUNT + 2, arm_hits + 2)
                elif dom_norm >= ARM_NORM:
                    arm_hits = min(ARM_COUNT + 2, arm_hits + 1)
                elif dom_norm <= 0.75:
                    arm_hits = max(0, arm_hits - 1)

                if arm_hits >= ARM_COUNT:
                    detected = True
                    release_hits = 0
            else:
                if dom_norm <= RELEASE_NORM:
                    release_hits += 1
                else:
                    release_hits = max(0, release_hits - 1)

                if release_hits >= RELEASE_COUNT:
                    detected = False
                    arm_hits = 0

            led.value(1 if detected else 0)

        if ticks_diff(now, last_print_ms) >= PRINT_EVERY_MS:
            print(
                "Current:", current_val,
                "Down:", int(down),
                "Up:", int(up),
                "NDown:", round(norm_down, 2),
                "NUp:", round(norm_up, 2),
                "PeakN:", round(peak_norm, 2),
                "Settle:", settling,
                "Arm:", arm_hits,
                "Rel:", release_hits,
                "T_down:", threshold_down,
                "T_up:", threshold_up,
                "Detect:", detected,
            )
            peak_norm = 0.0
            last_print_ms = now

        sleep_ms(15)

    except KeyboardInterrupt:
        print("Stopping...")
        led.value(0)
        break
