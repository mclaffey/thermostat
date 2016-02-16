import logging

from helpers import ThermostatException, Clock
from heater import HeaterControl


class Thermostat(object):
    available_modes = ['off', 'on', 'target']
    current_mode = 'off'
    _logger = logging.getLogger(__name__)
    target_temp = None
    # Actions occur when temperature exceeds thresholds, not simply when it reaches the threshold.
    # For example, if low threshold is 67, heater will kick on when temperature hits 66 or less.
    threshold_low = None
    threshold_high = None
    target_maximum = 82
    target_minimum = 40
    crossed_below_low_threshold_at = None
    crossed_above_high_threshold_at = None
    threshold_time_delay = 5 * 60 # 5 minutes

    def __init__(self, heater=HeaterControl(), thermometer=None, clock=Clock()):
        self.heater = heater
        self.clock = clock
        self.thermometer = thermometer

    def iterate(self):

        # report
        self._logger.debug("starting iterate() - mode={m}, heater={h}, temp={t}, targets={x}, clock={c}".format( \
            m=self.current_mode,
            h="on" if self.get_heater_is_on() else "off",
            t=self.get_room_temperature(),
            x="{}/{}/{}".format(self.threshold_low, self.target_temp, self.threshold_high),
            c=self.clock.time()
        ))

        self.check_thresholds()

        if self.current_mode == "target":
            # if we've been below threshold and...
            #    the heater isn't currently on and...
            #    we've been below threshold long enough
            # then turn on heater
            if self.crossed_below_low_threshold_at is not None and \
                not self.get_heater_is_on() and \
                    (self.clock.time() >= (self.crossed_below_low_threshold_at + self.threshold_time_delay)):
                    self._logger.info("Too long below threshold, turning on heater")
                    self.heater.set_to_on(True)

            # opposite above for turning off heater
            if self.crossed_above_high_threshold_at is not None and \
                self.get_heater_is_on() and \
                    (self.clock.time() >= (self.crossed_above_high_threshold_at + self.threshold_time_delay)):
                    self._logger.info("Too long above threshold, turning off heater")
                    self.heater.set_to_on(False)

        # iterate the heater
        self.heater.iterate()

    def get_heater_is_on(self):
        return self.heater.is_on()

    def set_mode(self, mode):
        if mode not in self.available_modes:
            raise ThermostatException("Unrecognized mode: {}".format(mode))

        if mode == "on":
            self.heater.set_to_on(True)
            self.heater.iterate()

        if mode == "off":
            self.heater.set_to_on(False)
            self.heater.iterate()

        if mode == "target":
            pass

        self.current_mode = mode
        self.iterate()

    def get_room_temperature(self):
        return self.thermometer.temperature

    def set_target_temperature(self, temp):
        if temp > self.target_maximum:
            raise ThermostatException("Can not set target above limit of {}".format(self.target_maximum))
        if temp < self.target_minimum:
            raise ThermostatException("Can not set target below limit of {}".format(self.target_minimum))
        self.target_temp = temp
        self.threshold_low = temp - 1
        self.threshold_high = temp + 1

    def get_target_temperature(self):
        return self.target_temp

    def check_thresholds(self):
        # record threshold crossings
        if self.threshold_low is not None:
            # if below low threshold
            if self.thermometer.temperature < self.threshold_low:
                if self.crossed_below_low_threshold_at is None:
                    self.crossed_below_low_threshold_at = self.clock.time()
                    self._logger.debug("Exceeded low threshold")
            # if at or above low threshold
            else:
                if self.crossed_below_low_threshold_at is not None:
                    self.crossed_below_low_threshold_at = None
                    self._logger.debug("Within low threshold");
        if self.threshold_high is not None:
            # if above high threshold
            if self.thermometer.temperature > self.threshold_high:
                if self.crossed_above_high_threshold_at is None:
                    self.crossed_above_high_threshold_at = self.clock.time()
                    self._logger.debug("Exceeded high threshold")
            # if at or below high threshold
            else:
                if self.crossed_above_high_threshold_at is not None:
                    self.crossed_above_high_threshold_at = None
                    self._logger.debug("Within high threshold")
