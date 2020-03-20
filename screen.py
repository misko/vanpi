#!/usr/bin/python3
import pyscreenshot as ImageGrab

def screen_grab():
    im = ImageGrab.grab()
    im.save('/home/pi/vanpi/screenshot.png')

screen_grab()


