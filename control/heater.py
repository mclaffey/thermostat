import logging

from helpers import Clock, ThermostatException


class AbstractHeater(object):
    _heater_is_on = False

    def is_on(self):
        return self._heater_is_on

    def set_to_on(self, val):
        self._heater_is_on = val


class HeaterCycleProtection(object):
    """Controls on/off of the heater and enforces cycle protection"""

    # a duration in seconds. do not run the heater for longer than this consecutively
    maximum_on_time = 60 * 60  # 1 hour

    # a duration in seconds. these are the cycle protection times. if turning on, the heater
    # must be allowed to run for the minimum time before being turned off.
    minimum_on_time = 5 * 60  # 5 minutes
    minimum_off_time = 5 * 60  # 5 minutes

    # a time in the future. do not turn the heater on or off before reaching these times
    # None means it is safe to turn on/off at any time
    _no_turn_on_before = None
    _no_turn_off_before = None

    # a time in the future, when it is scheduled to turn heater on or off
    _turn_on_time = None
    _turn_off_time = None

    # a time in the past, when the heater was turned on or off
    _on_since = None
    _off_since = None

    # boolean. indicates what state the user wants. it may be different from the actual heater state.
    # for example, intended might be OFF (False), but due to cycle protection, the heater is still
    # running for a few more minutes
    _intended_on = False
    _actually_on = False

    _logger = logging.getLogger(__name__)

    def __init__(self, heater, clock=None):
        """

        :param heater: the underlying heater being controlled. See AbstractHeater.
        :param clock: the instance used to determine time. This is only here to facilitate
        testing. In production, the default should be used.
        :return:
        """
        self._heater = heater

        if clock:
            self._clock = clock
        else:
            self._clock = Clock()

    def is_on(self):
        """Returns the intended state of the heater.

        For example, the heater can be set to off, but it hasn't turned off yet
        because the cycle protection won't allow it. This method will return
        False, but is_heather_actually_on() will return True.
        """
        return self._intended_on

    def is_actually_on(self):
        """The true state of the heater, which may be different than the intended/reported
        state due to cycle protection.
        """
        return self._heater.is_on()

    def set_to_on(self, val):
        """Sets the intended state of the heater.

        :parameter val - True to turn heater on, False to turn heater off

        This method doesn't actually turn the heater on or off. It just schedules
        a time to do so, which in most cases could be immediately. For that to take
        effect, the calling code must call the .iterate() method.

        The change won't take effect immediately if the cycle protection
        is in effect.
        """

        # turning on
        if val:
            self._intended_on = True
            # intend to turn on but heater is not currently on
            if not self._actually_on:
                self._turn_on_time = max(self._no_turn_on_before, self._clock.time())
                self._turn_off_time = None
                self._logger.debug("Set to turn on at: {}".format(self._turn_on_time))

        # turning off
        else:
            self._intended_on = False
            # intend to turn off but heater is not currently off
            if self._actually_on:
                self._turn_on_time = None
                self._turn_off_time = max(self._no_turn_off_before, self._clock.time())
                self._logger.debug("Set to turn off at: {}".format(self._turn_off_time))

    def iterate(self):

        already_handled = False

        # if we passed the turn off time
        if self._turn_off_time is not None and self._turn_off_time <= self._clock.time():
            # if the time was set before the cycle protection, log message and push the time back
            if self._no_turn_off_before and self._no_turn_off_before > self._turn_off_time:
                self._logger.warn(
                    "Turn off time was set before cycle protection. Will not turn off until cycle protection is over.")
                self._turn_off_time = self._no_turn_off_before

            # otherwise turn off
            self._logger.info("Reached turn off time. Turning off.")
            self._heater.set_to_on(False)
            self._turn_off_time = None
            self._turn_on_time = None
            self._on_since = None
            self._off_since = self._clock.time()
            self._no_turn_off_before = None
            self._no_turn_on_before = self._clock.time() + self.minimum_off_time

            already_handled = True

        # if we passed the turn on time
        if self._turn_on_time is not None and self._turn_on_time <= self._clock.time():
            if already_handled:
                raise ThermostatException("Already handled, this probably shouldn't be happening")
            # if this would turn on before the cycle protection, log message and push the time back
            if self._no_turn_on_before and self._no_turn_on_before > self._turn_on_time:
                self._logger.warn(
                    "Turn on time was set before cycle protection. Will not turn on until cycle protection is over.")
                self._turn_on_time = self._no_turn_on_before

            # otherwise turn on
            self._logger.info("Reached turn on time. Turning on.")
            self._heater.set_to_on(True)
            self._turn_off_time = None
            self._turn_on_time = None
            self._on_since = self._clock.time()
            self._off_since = None
            self._no_turn_off_before = self._clock.time() + self.minimum_on_time
            self._no_turn_on_before = None

            already_handled = True

        # if we passed the maximum on time
        if self._on_since is not None and (self._clock.time() - self._on_since) >= self.maximum_on_time:
            if already_handled:
                raise ThermostatException("Already handled, this probably shouldn't be happening")
            self._logger.warn("Reached maximum consecutive on time. Scheduling for shutdown.")
            self._heater.set_to_on(False)
            self.iterate()
