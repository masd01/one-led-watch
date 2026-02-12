"""
One LED Watch για Raspberry Pi Pico (RP2040)
MicroPython version

Εμφανίζει την ώρα με ένα LED:
- Ώρα 1–12 → 12 παλμοί 2sec
- Τέταρτα → 0–3 παλμοί 1sec
- Λεπτά mod 15 → 0–14 παλμοί 0.5sec
Παύση 1sec μεταξύ ομάδων.

Κουμπί: πατήστε για προβολή ώρας.
Pico κοιμάται μεταξύ δευτερολέπτων (εξοικονόμηση ενέργειας).
"""

import machine
import utime
import uasyncio as asyncio
from machine import Pin, Timer, RTC

# ------------------------------------------------------------
# ΡΥΘΜΙΣΕΙΣ
# ------------------------------------------------------------
LED_PIN = 25          # GP25 – internal LED
BUTTON_PIN = 2       # GP2 – Κουμπί (με pull-up)

# ------------------------------------------------------------
# ΚΑΤΑΣΤΑΣΗ ΡΟΛΟΓΙΟΥ (12-ωρη μορφή)
# ------------------------------------------------------------
hour = 5
minute = 43
second = 0
ampm = 0            # 0=AM, 1=PM – ΔΕΝ ΕΜΦΑΝΙΖΕΤΑΙ

# ------------------------------------------------------------
# ΑΡΧΙΚΟΠΟΙΗΣΗ
# ------------------------------------------------------------
led = Pin(LED_PIN, Pin.OUT)
led.value(0)

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Εσωτερικό RTC για ακριβή χρονομέτρηση
rtc = RTC()

# Σημαίες για ασύγχρονη λειτουργία
button_pressed = False
time_updated = False

# ------------------------------------------------------------
# ΔΙΑΚΟΠΗ ΚΟΥΜΠΙΟΥ
# ------------------------------------------------------------
def button_handler(pin):
    global button_pressed
    # Debounce: μικρή καθυστέρηση και έλεγχος
    utime.sleep_ms(20)
    if pin.value() == 0:
        button_pressed = True

button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

# ------------------------------------------------------------
# ΧΡΟΝΟΜΕΤΡΗΤΗΣ 1sec (Timer)
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
            # Εναλλαγή AM/PM όταν πάμε από 11 σε 12
            if old_hour == 11 and hour == 12:
                ampm = not ampm
    time_updated = True

# Εκκίνηση timer κάθε 1000ms (1sec)
timer.init(period=1000, mode=Timer.PERIODIC, callback=tick)

# ------------------------------------------------------------
# ΕΜΦΑΝΙΣΗ ΩΡΑΣ ΜΕ LED
# ------------------------------------------------------------
async def display_time(h, m):
    """Εμφανίζει ώρα και λεπτά με παλμούς LED."""
    
    # 1) ΩΡΑ: h παλμοί 2000ms
    if h > 0:
        await flash_group(h, 1000, 500)
        await asyncio.sleep(1)      # παύση 1sec
    
    # 2) ΤΕΤΑΡΤΑ: m/15 παλμοί 1000ms
    quarters = m // 15
    if quarters > 0:
        await flash_group(quarters, 500, 500)
        await asyncio.sleep(1)      # παύση 1sec
    
    # 3) ΛΕΠΤΑ mod 15: m%15 παλμοί 500ms
    minutes_mod = m % 15
    if minutes_mod > 0:
        await flash_group(minutes_mod, 250, 500)
    # ΧΩΡΙΣ τελική παύση

async def flash_group(count, on_time, off_time):
    """Αναβοσβήνει LED 'count' φορές με διάρκεια on/off."""
    for i in range(count):
        led.value(1)
        await asyncio.sleep_ms(on_time)
        led.value(0)
        if i < count - 1:
            await asyncio.sleep_ms(off_time)

# ------------------------------------------------------------
# ΚΥΡΙΑ ΑΣΥΓΧΡΟΝΗ ΣΥΝΑΡΤΗΣΗ
# ------------------------------------------------------------
async def main():
    global button_pressed, time_updated, hour, minute
    
    print("One LED Watch για Pico – εκκίνηση...")
    print(f"Αρχική ώρα: {hour:02d}:{minute:02d} {'PM' if ampm else 'AM'}")
    
    while True:
        # Έλεγχος για πάτημα κουμπιού
        if button_pressed:
            button_pressed = False
            
            # Απενεργοποίηση διακοπής κουμπιού προσωρινά
            button.irq(handler=None)
            
            # Εμφάνιση τρέχουσας ώρας
            cur_hour = hour
            cur_minute = minute
            print(f"Εμφάνιση ώρας: {cur_hour:02d}:{cur_minute:02d}")
            await display_time(cur_hour, cur_minute)
            
            # Debounce: περιμένουμε να αφεθεί το κουμπί
            while button.value() == 0:
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(50)
            
            # Επανενεργοποίηση διακοπής
            button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
        
        # Μικρή αναμονή για εξοικονόμηση ενέργειας
        await asyncio.sleep_ms(100)

# ------------------------------------------------------------
# ΕΚΚΙΝΗΣΗ
# ------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())