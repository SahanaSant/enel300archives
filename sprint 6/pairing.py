from machine import UART, Pin
import time

# Master HC-05 is connected on UART1:
# Pico GP8 (TX)  -> HC-05 RX
# Pico GP9 (RX)  -> HC-05 TX
uart_master = UART(1, baudrate=38400, tx=Pin(8), rx=Pin(9), timeout=1200)

# Slave HC-05 is left in NORMAL mode (KEY/EN LOW), discoverable.
# Use the slave address in HC-05 bind format: xxxx,yy,zzzzzz
SLAVE_ADDR = "2025,08,005326"

# Keep master in full AT mode while running this script:
# 1) KEY/EN HIGH before power-up
# 2) LED slow blink


def _read_all(u):
    chunks = []
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < 900:
        if u.any():
            data = u.read()
            if data:
                chunks.append(data)
            start = time.ticks_ms()
        else:
            time.sleep_ms(30)
    if not chunks:
        return ""
    return b"".join(chunks).decode("utf-8", "ignore").strip()


def send_at(u, cmd, wait_ms=500):
    while u.any():
        u.read()
    u.write(cmd + "\r\n")
    time.sleep_ms(wait_ms)
    resp = _read_all(u)
    print(cmd, "=>", resp if resp else "(no reply)")
    return resp


def set_master_role(u):
    resp = send_at(u, "AT+ROLE=1")
    if not resp:
        send_at(u, "AT+ROLE1")


def configure_master_only(u, slave_addr):
    print("=== Master-only pairing ===")
    send_at(u, "AT")
    send_at(u, "AT+VERSION?")
    set_master_role(u)
    send_at(u, "AT+CMODE=0")
    send_at(u, "AT+PSWD=1234")
    send_at(u, "AT+BIND=" + slave_addr)
    send_at(u, "AT+INIT")
    send_at(u, "AT+PAIR=" + slave_addr + ",20", 1800)
    send_at(u, "AT+LINK=" + slave_addr, 1800)


def main():
    configure_master_only(uart_master, SLAVE_ADDR)
    print("\nIf commands replied, now power-cycle MASTER with KEY/EN LOW.")
    print("Run both main scripts in normal mode at 9600 baud.")


main()


