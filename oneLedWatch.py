"""
One LED Watch for Raspberry Pi Pico (RP2040)
MicroPython version

- Hours 1–12 → 12 pulse 1sec
- Quarters → 0–3 pulse 0.5sec
- Minutes mod 15 → 0–14 pulse 0.25sec
Pause 1sec in between.

Button: push to see time. Don't forget to count!
Pico sleeps between secs (energy saver).

github.com/masd01
"""

import machine
import utime
import uasyncio as asyncio
from machine import Pin, Timer, RTC

# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------
LED_PIN = 25          # GP25 – internal LED
BUTTON_PIN = 2       # GP02 – Button (with pull-up)

# ------------------------------------------------------------
# Watch State (12h) set starting time
# ------------------------------------------------------------
hour = 5         
minute = 43
second = 0
ampm = 0            # 0=AM, 1=PM 

# ------------------------------------------------------------
# Initialization
# ------------------------------------------------------------
led = Pin(LED_PIN, Pin.OUT)
led.value(0)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Internal RTC for precise time count
rtc = RTC()

# Flags for asyncio function
button_pressed = False
time_updated = False

# ------------------------------------------------------------
# Push Button
# ------------------------------------------------------------
def button_handler(pin):
    global button_pressed
    # Debounce: slow delay and control
    utime.sleep_ms(20)
    if pin.value() == 0:
        button_pressed = True

button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

# ------------------------------------------------------------
# Timer 1sec 
# ------------------------------------------------------------
timer = Timer()

def tick(t):
    global second, minute, hour, ampm, time_updated
    second += 1
    if second >= 60:
        second = 0
        minute += 1
        if minute >= 60:
            minute = 0
            old_hour = hour
            hour += 1
            if hour > 12:
                hour = 1
            # change AM/PM from 11 to 12
            if old_hour == 11 and hour == 12:
                ampm = not ampm
    time_updated = True

# Start timer every 1000ms (1sec)
timer.init(period=1000, mode=Timer.PERIODIC, callback=tick)

# ------------------------------------------------------------
# Show time with LED
# ------------------------------------------------------------
async def display_time(h, m):
    """Shows time with LED pulses."""
    
    # 1) Hour: h pulses 1000ms
    if h > 0:
        await flash_group(h, 1000, 500)
        await asyncio.sleep(1)      # pause 1sec
    
    # 2) Quarters: m/15 pulses 500ms
    quarters = m // 15
    if quarters > 0:
        await flash_group(quarters, 500, 500)
        await asyncio.sleep(1)      # pause 1sec
    
    # 3) Minutes mod 15: m%15 pulses 250ms
    minutes_mod = m % 15
    if minutes_mod > 0:
        await flash_group(minutes_mod, 250, 500)
    # NO final pause

async def flash_group(count, on_time, off_time):
    """Blinks LED 'count' times with duration on/off."""
    for i in range(count):
        led.value(1)
        await asyncio.sleep_ms(on_time)
        led.value(0)
        if i < count - 1:
            await asyncio.sleep_ms(off_time)

# ------------------------------------------------------------
# Main asyncio function
# ------------------------------------------------------------
async def main():
    global button_pressed, time_updated, hour, minute
    
    print("One LED Watch for Pico – starting...")
    print(f"Start time: {hour:02d}:{minute:02d} {'PM' if ampm else 'AM'}")
    
    while True:
        # Check button
        if button_pressed:
            button_pressed = False
            
            # Disable button stop temporarily
            button.irq(handler=None)
            
            # Show current time
            cur_hour = hour
            cur_minute = minute
            print(f"Show time: {cur_hour:02d}:{cur_minute:02d}")
            await display_time(cur_hour, cur_minute)
            
            # Debounce: wait button release
            while button.value() == 0:
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(50)
            
            # Enable button stop
            button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
        
        # Slow delay for energy save
        await asyncio.sleep_ms(100)

# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":

    asyncio.run(main())
