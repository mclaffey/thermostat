#!/usr/bin/env python

import sqlite3
import pandas as pd

# #########################
# room data
db_room = sqlite3.connect("../data/therm.db")
room = pd.read_sql("SELECT read_time as date, temperature as temp FROM temp", db_room)

# remove rows that don't differ by more than 0.5 degrees
i_is_diff = (room.temp.diff().abs() > 0)
room = room[i_is_diff]
print "Kept values: {}, {:%}".format( room.shape[0], i_is_diff.mean())

room.to_csv("public_html/room.tsv", sep="\t", index=False)

# #########################
# weather data
db_weather = sqlite3.connect("../data/weather.db")
weather = pd.read_sql("SELECT datetime as date, temperature_f as temp FROM readings ORDER BY datetime", db_weather)
weather.to_csv("public_html/weather.tsv", sep="\t", index=False)