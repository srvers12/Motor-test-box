from machine import Pin,PWM
import utime



led = Pin(25,Pin.OUT)

list = [led]
toggleFlg = False

while True:
    if toggleFlg == True:
        list[0].value(1)
    else:
        list[0].value(0)
    toggleFlg = not toggleFlg
    utime.sleep_ms(500)

    