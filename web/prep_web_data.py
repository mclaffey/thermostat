#!/usr/bin/env python

import sqlite3
import pandas as pd

# #########################
# room data
db_room = sqlite3.connect("../data/therm.db")
room = pd.read_sql("SELECT read_time as date, temperature as temp FROM temp", db_room)

# remove rows that don't differ by more than 0.5 degrees
i_is_diff = (room.temp.diff().abs() > 0)
i_is_diff.iloc[-1] = True # always keep the last record
room = room[i_is_diff]
print "Kept values: {}, {:%}".format( room.shape[0], i_is_diff.mean())
print room.tail()
room.to_csv("public_html/room.tsv", sep="\t", index=False)

# #########################
# weather data
db_weather = sqlite3.connect("../data/weather.db")
weather = pd.read_sql("SELECT datetime as date, temperature_f as temp FROM readings ORDER BY datetime", db_weather)
weather.to_csv("public_html/weather.tsv", sep="\t", index=False)
<<<<<<< HEAD

# #########################
# forecast data
db_forecast = sqlite3.connect("../data/forecast.db")
forecast = pd.read_sql("SELECT forecast_datetime as date, temperature as temp FROM forecasts WHERE is_latest=1 ORDER BY forecast_datetime", db_forecast)
forecast.to_csv("public_html/forecast.tsv", sep="\t", index=False)
=======
print weather.tail()
>>>>>>> b9ba29afde7cd761e74145299485f315f0850ae6
