class Thermostat(object):
    thermometer = None
    clock = None

    def __init__(self, _heater, thermometer, clock=None):
        self.thermometer = thermometer
        self.available_modes = ['off', 'on', 'auto']
        self.current_mode = 'off'

        if _heater:
            self.heater = _heater
        else:
            self.heater = HeaterControl()

        if clock:
            self.clock = clock
        else:
            self.clock = Clock()

        self.threshold_low = None
        self.target_temp = None
        self.threshold_high = None

    def iterate(self):
        room_temp = self.get_room_temperature()
        if room_temp < self.threshold_low:
            self.heater.set_to_on(True)
        if room_temp > self.threshold_high:
            self.heater.set_to_on(False)
        self.heater.iterate()

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
