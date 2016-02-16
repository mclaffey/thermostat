import random
import logging
from unittest import TestCase

from heater import HeaterCycleProtection

logging.basicConfig(level=logging.DEBUG)


class TestClock(object):
    """An clock whos time can be manipulated, for use in testing

    A real thermometer will use a class with a single method .time(), which
    returns the current time as returned be the .time() method in python's
    time module.

    This test clock therefore has a .time() method that will be used by a thermostat
    during testing. Instead of returning the actual time, it returns whatever time
    the tester has set it to.

    Note: As of 2016, python's time.time() returns a float somewhere around 1.5 billion.
    This test clock starts at time 0 for simplicity. All use of the clock should be
    based on relative differences anyways.
    """

    def __init__(self):
        self._time = 0

    def time(self):
        return self._time

    def set_clock(self, the_time):
        self._time = the_time

    def advance(self, minutes=0):
        self._time += (minutes * 60)

    def advance_random(self):
        self.advance(minutes=random.randint(1, 10))


class TestHeaterControl(TestCase):
    def setUp(self):
        self.clock = TestClock()
        self.heater = HeaterCycleProtection(self.clock)

    def test_turn_on(self):
        self.heater.set_to_on(True)
        self.heater.iterate()
        self.assertTrue(self.heater._intended_on)
        self.assertTrue(self.heater._actually_on)

    def test_turn_off(self):
        self.heater.set_to_on(False)
        self.heater.iterate()
        self.assertFalse(self.heater._intended_on)
        self.assertFalse(self.heater._actually_on)

    def test_dont_cycle_off_heater_too_quickly(self):
        self.heater.set_to_on(True)
        self.heater.iterate()
        # advance 1 minute
        self.clock.advance(minutes=1)
        # try to turn off, but heater won't allow it
        self.heater.set_to_on(False)
        self.assertFalse(self.heater._intended_on)
        self.assertTrue(self.heater._actually_on)
        # go the rest of the time so that heater can turn off
        self.clock.advance(minutes=4)
        self.heater.iterate()
        self.assertFalse(self.heater._intended_on)
        self.assertFalse(self.heater._actually_on)

    def test_dont_cycle_on_heater_too_quickly(self):
        # even though the heater starts off, if we explicitly set it to off, this will start
        # the cycle protection
        self.heater.set_to_on(False)
        self.heater.iterate()
        # advance 2 minutes
        self.clock.advance(minutes=2)
        # try to turn on, but heater won't allow it
        self.heater.set_to_on(True)
        self.assertTrue(self.heater._intended_on)
        self.assertFalse(self.heater._actually_on)
        # go the rest of the time so that heater can turn off
        self.clock.advance(minutes=3)
        self.heater.iterate()
        self.assertTrue(self.heater._intended_on)
        self.assertTrue(self.heater._actually_on)
