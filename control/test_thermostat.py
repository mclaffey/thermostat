import random
import logging
from unittest import TestCase

from helpers import ThermostatException
from thermostat import Thermostat
from heater import HeaterCycleProtection
from test_heaterControl import TestClock

logging.basicConfig(level=logging.DEBUG)


class TestThermometer(object):
    def __init__(self):
        self.temperature = None


class FailHelper(TestCase):
    """This is a kludge to be able to call unittest.TestCase.fail() from outside the class.

    Usage: FailHelper().do_fail("I'm failing because...")
    """
    def runTest(self):
        pass

    def do_fail(self, msg):
        self.fail(msg)


class TestHeater(object):
    def __init__(self):
        self.exception_if_turned_on = True
        self.exception_if_turned_off = True
        self._is_turned_on = False

    def set_to_on(self, val=True):
        if val:
            if self.exception_if_turned_on:
                FailHelper().do_fail("Heater not allowed to turn on now")
            self._is_turned_on = True
        else:
            if self.exception_if_turned_off:
                FailHelper().do_fail("Heater not allowed to turn off now")
            self._is_turned_on = False

    def is_on(self):
        return self._is_turned_on

    def iterate(self):
        pass


class TestThermostat(TestCase):

    @classmethod
    def setUpClass(cls):
        random.seed(0)

    def setUp(self):
        # create instances
        self.heater = TestHeater()
        self.thermometer = TestThermometer()
        self.clock = TestClock()
        self.thermostat = Thermostat(self.heater, self.thermometer, self.clock)

        # setup testing environment
        # in the beginning, temperature is above threshold, heater is off, both exceptions are on
        self.clock.set_clock(0)
        self.thermometer.temperature = 68
        self.heater._is_turned_on = False
        self.heater.exception_if_turned_on = True
        self.heater.exception_if_turned_off = True

        # start thermostat in target mode with target=68 (thresholds of 67/69)
        self.thermostat.set_target_temperature(68)
        self.thermostat.set_mode('target')


    def test_read_heater_status(self):
        # turn on
        self.heater.exception_if_turned_on = False
        self.heater.set_to_on(True)
        self.assertTrue(self.thermostat.get_heater_is_on())
        # turn off
        self.heater.exception_if_turned_off = False
        self.heater.set_to_on(False)
        self.assertFalse(self.thermostat.get_heater_is_on())

    def test_turn_on_heater_manually(self):
        # turn on
        self.heater.exception_if_turned_on = False
        self.thermostat.set_mode("on")
        self.assertTrue(self.heater.is_on())

    def test_turn_off_heater_manually(self):
        # turn off heater
        self.heater.exception_if_turned_off = False
        self.thermostat.set_mode("off")
        self.assertFalse(self.heater.is_on())

    def test_read_thermometer(self):
        for temp in [0, -5, 98.6]:
            self.thermometer.temperature = temp
            self.assertEquals(self.thermostat.get_room_temperature(), temp)

    def test_set_point(self):
        for temp in [40, 68, 82]:
            self.thermostat.set_target_temperature(temp)
            self.assertEquals(self.thermostat.get_target_temperature(), temp)
            self.assertLess(self.thermostat.threshold_low, temp)
            self.assertGreater(self.thermostat.threshold_high, temp)

    def test_set_point_too_low(self):
        temp = 39  # min allowable is 40
        with self.assertRaises(ThermostatException):
            self.thermostat.set_target_temperature(temp)

    def test_set_point_too_high(self):
        temp = 83  # max allowable is 82
        with self.assertRaises(ThermostatException):
            self.thermostat.set_target_temperature(temp)

    def test_turn_heater_on_when_too_cold(self):
        # after 5 minutes below at or below .threshold_low(), turns on heater
        # advance to some arbitrary time, go below threshold
        self.clock.advance_random()
        self.thermometer.temperature = 66
        self.thermostat.iterate()
        # advance less than the required time, heater still off
        self.clock.advance(minutes=4.9)
        self.thermostat.iterate()
        # advance to the required time, heater should kick on
        self.clock.advance(minutes=0.1)
        self.heater.exception_if_turned_on = False
        self.thermostat.iterate()
        self.assertTrue(self.heater.is_on())

    def helper_get_cold_to_trigger_heater(self):
        # possible unintended consequences if not run as first line in test
        # advance to some arbitrary time, it is now too cold
        self.clock.advance_random()
        self.thermometer.temperature = 66
        self.thermostat.iterate()
        # stay cold long enough for heater to kick on
        self.clock.advance(minutes=5)
        self.heater.exception_if_turned_on = False
        self.thermostat.iterate()
        self.assertTrue(self.heater.is_on())

    def test_turn_heater_on_when_too_cold_helper(self):
        self.helper_get_cold_to_trigger_heater()

    def test_dont_heat_up_if_not_cold_long_enough(self):
        # threshold duration is 5 minutes. heater should not turn on if cold for 4, warm for 1, cold for 4
        # advance to some arbitrary time, go below threshold
        self.clock.advance_random()
        self.thermometer.temperature = 66
        self.thermostat.iterate()
        # advance less than the required time, heater still off
        self.clock.advance(minutes=4)
        self.thermostat.iterate()
        # advance 1 minute, but temperature is above threshold now
        self.clock.advance(minutes=1)
        self.thermometer.temperature = 68
        self.thermostat.iterate()
        # advance 1 minute, temperature back below threshold
        self.clock.advance(minutes=1)
        self.thermometer.temperature = 66
        self.thermostat.iterate()
        # advance less than the required time, heater still off
        self.clock.advance(minutes=4)
        self.thermostat.iterate()

    def test_keep_heater_on_until_warm_enough(self):
        self.helper_get_cold_to_trigger_heater()
        # advance arbitrary amount of time, heater is still on
        # this arbitrary time must be less than the maximum-on-duration (20 minutes)
        self.clock.advance(minutes=7.2)
        self.thermostat.iterate()
        # come above threshold, heater will run until above for 5 minutes
        # total arbitrary time must be less than the maximum-on-duration (20 minutes)
        self.clock.advance(minutes=4.8)
        self.thermometer.temperature = 70
        self.thermostat.iterate()
        # advance 5 minutes
        self.clock.advance(minutes=5)
        self.heater.exception_if_turned_off = False
        self.thermostat.iterate()
        self.assertFalse(self.heater.is_on())

    # def test_dont_cycle_off_heater_too_quickly(self):
    #     self.helper_get_cold_to_trigger_heater()
    #     # advance 1 minute, already warm enough, but don't cycle off heater yet
    #     self.clock.advance(minutes=1)
    #     self.thermometer.temperature = 70
    #     self.thermostat.iterate()
    #     # advance to just under cycle minimum time on, heater should still be on
    #     self.clock.advance(minutes=3.9)
    #     self.thermostat.iterate()
    #     # advance beyond cycle minimum time on, heater should turn off
    #     self.clock.advance(minutes=0.1)
    #     self.heater.exception_if_turned_off = False
    #     self.thermostat.iterate()
    #     self.assertFalse(self.heater.is_on())
    #
    # def test_dont_cycle_on_heater_too_quickly(self):
    #     # the beginning of this test needs to trigger the heater and let things warm up
    #     self.helper_get_cold_to_trigger_heater()
    #     # advance and warm up
    #     self.clock.advance(minutes=10)
    #     self.thermometer.temperature = 70
    #     self.heater.exception_if_turned_off = False
    #     self.thermostat.iterate()
    #     self.assertFalse(self.heater.is_on())
    #     # the heater is off now, but throw exception if thermostat tries to turn if off again
    #     self.heater.exception_if_turned_off = True
    #     # now quickly get cold again, but don't turn on heater yet
    #     self.clock.advance(minutes=1)
    #     self.thermometer.temperature = 66
    #     self.thermostat.iterate()
    #     # advance to just inside cycle limit, still not on yet
    #     self.clock.advance(minutes=3.9)
    #     self.thermostat.iterate()
    #     # advance to just outside of cycle limit, heater should kick on
    #     self.clock.advance(minutes=0.1)
    #     self.heater.exception_if_turned_on = False
    #     self.thermostat.iterate()
    #     self.assertTrue(self.heater.is_on())

    def test_dont_keep_heater_on_forever(self):
        # use the real heater controller, not the test heater
        self.heater = HeaterCycleProtection(self.clock)
        self.thermostat = Thermostat(self.heater, self.thermometer, self.clock)
        self.thermostat.set_mode('on')
        # advance to just before time limit
        self.clock.advance(minutes=59)
        self.thermostat.iterate()
        self.assertTrue(self.heater.is_on())
        # advance past limit, heater should go off
        self.clock.advance(minutes=1)
        self.thermostat.iterate()
        self.assertFalse(self.heater.is_on())
