import time


class ThermostatException(Exception):
    pass


class Clock(object):

    @classmethod
    def time(cls):
        return time.time()

class Thermostat(object):
    heater = None
    thermometer = None
    clock = None

    def __init__(self, heater, thermometer, clock=None):
        self.heater = heater
        self.thermometer = thermometer
        self.available_modes = ['off', 'on', 'auto']
        self.current_mode = 'off'

        if clock:
            self.clock = clock
        else:
            self.clock = Clock()

        self.threshold_low = None
        self.target_temp = None
        self.threshold_high = None

    def iterate(self):
        pass

    def get_heater_is_on(self):
        return self.heater.is_on()

    def set_mode(self, mode):
        if mode not in self.available_modes:
            raise ThermostatException("Unrecognized mode: {}".format(mode))
        self.current_mode = mode

    def set_heater_to_on(self, val):
        pass

    def get_room_temperature(self):
        return self.thermometer.temperature

    def set_target_temperature(self, temp):
        self.target_temp = temp
        self.threshold_low = temp - 1
        self.threshold_high = temp + 1

    def get_target_temperature(self):
        return self.target_temp
