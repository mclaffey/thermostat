#!/usr/bin/env python
import RPi.GPIO as pi
import time  
import sys
import os
import ctypes, os

# check that running as admin
def exit_if_not_admin():
	try:
	        is_admin = os.getuid() == 0
	except AttributeError:
	        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
	if not is_admin:
	        sys.exit("Must run as administrator")

class PinController(object):

	pin_num = 11
	pin_state = None

	def __init__(self):
		pi.setmode(pi.BOARD)  
		pi.setup(self.pin_num, pi.OUT)
		self.pin_state = pi.input(self.pin_num)

	def turn_on(self):
		pi.output(self.pin_num, pi.HIGH)

	def turn_off(self):
		pi.output(self.pin_num, pi.LOW)

	def blink(self, times=5):
		for i in range(0, times):
			self.turn_on()
			time.sleep(0.1)
			self.turn_off()
			time.sleep(0.1)

	def cleanup(self):
		pi.cleanup()

if __name__ == '__main__':
	exit_if_not_admin()
	print "Starting"
	pin = PinController()
	pin.blink()
	pin.cleanup()
	print "Done"

