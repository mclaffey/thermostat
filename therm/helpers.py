import time


class ThermostatException(Exception):
    pass


class Clock(object):

    @classmethod
    def time(cls):
        return time.time()