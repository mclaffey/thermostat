#!/usr/bin/env python
"""Poll for last 48 hours of weather

This queries http://w1.weather.gov/obhistory/KCLT.html, which only provides the last 48 hours.

This includes functionality to create a database to house past entries. The intention is that
the script can be called hourly to keep the database populated with the lastest entry while also
building a history.

Example use:

import weather

# RUN ONLY ONCE!
import sqlite3
db = sqlite3.connect('weather.db')
weather.setup_table(db)

# Repeated use
weather.query_and_save('weather.db')


TODO:
CRITICAL - smarter dates - it uses the current month even when the last 48 hours includes the previous month
INSERT OR IGNORE instead of individual try-catch


"""

import sys
import pandas as pd
import datetime
import sqlite3
import os


def query_and_save(db_path, verbose=False):
	"""Query the web and add new records to database
	"""
	db = sqlite3.connect(db_path)
	data1 = query_weather_web(verbose)
	data2 = clean_weather_table(data1)
	result = append_records(db, data2, verbose)
	return result

def query_weather_web(verbose=False):
	"""Query the website for the table of weather data
	"""
	if verbose:
		print "Querying website...",
		sys.stdout.flush()
	website_tables = pd.read_html("http://w1.weather.gov/obhistory/KCLT.html")
	if verbose:
		print "Done"

	weather_table = website_tables[3].copy()
	return weather_table

def clean_weather_table(weather_table):
	data = weather_table.copy()

	# column names
	data.columns = col_labels

	# drop these columns which contain aggregate data
	data.drop(['temp_6hr_max', 'temp_6hr_min', 'precipitation_3hr', 'precipitation_6hr'], axis=1, inplace=True)

	# remove the header and footer
	# this should be the top 3 and bottom 3 rows. But here I'll look for any rows that don't have an integer
	# in the day column
	def is_int(x):
	    try:
	        int(x)
	        return True
	    except:
	        return False
	i_is_int = (data.day.apply(is_int))
	data = data[i_is_int]

	# remove % from humidity
	data.humidity = data.humidity.apply(lambda x: x.replace("%", ""))

	# make a date_time column
	data['month'] = datetime.datetime.today().month
	data['year'] = datetime.datetime.today().year
	data['datetime'] = data.month.apply(str) + "/" + data.day.apply(str) + "/" + data.year.apply(str) \
	    + " " + data.time.apply(str)
	data['datetime'] = pd.to_datetime(data.datetime)

	# put the datetime column first and get rid of the redudant columns
	data.drop(['day', 'month', 'year', 'time'], axis=1, inplace=True)
	cols = ['datetime'] + [_ for _ in data.columns if _ is not 'datetime']
	data = data[cols]

	# convert columns to numeric
	for col in ['vis_mi', 'temperature_f', 'dewpoint_f', 'humidity', 'wind_chill_f', 'heat_index_f',
	            'pressure_in', 'pressure_mb', 'precipitation']:
	    data[col] = pd.to_numeric(data[col], errors='raise')

	return data

def setup_table(db):
	"""Creates the readings table in the databsae (drop if already exists)
	"""
	sql = """
	CREATE TABLE readings (
	  datetime TIMESTAMP PRIMARY KEY,
	  wind_mph TEXT,
	  vis_mi NUMERIC,
	  weather TEXT,
	  sky TEXT,
	  temperature_f NUMERIC,
	  dewpoint_f NUMERIC,
	  humidity NUMERIC,
	  wind_chill_f NUMERIC,
	  heat_index_f NUMERIC,
	  pressure_in NUMERIC,
	  pressure_mb NUMERIC,
	  precipitation NUMERIC
	)
	"""
	db.execute("DROP TABLE IF EXISTS readings")
	db.execute(sql)
	db.commit()

def append_records(db, data, verbose=False):
	"""Add records to database

	Any records that already exist in the databse are not re-added (no duplicates are created.)
	"""
	added = 0
	duplicated = 0
	if verbose:
		print "Adding records...",
		sys.stdout.flush()
	for i,row in data.iterrows():
	    row = row.to_frame().T
	    row.set_index('datetime', inplace=True)
	    try:
	        row.to_sql("readings", db, if_exists='append')
	        added += 1
	    except sqlite3.IntegrityError:
	        duplicated += 1        
	db.commit()
	
	if verbose:
		print "{} added, {} already existed".format(added, duplicated)
	return (added, duplicated)


# column headings for table on http://w1.weather.gov/obhistory/KCLT.html
col_labels="""
day
time
wind_mph
vis_mi
weather
sky
temperature_f
dewpoint_f
temp_6hr_max
temp_6hr_min
humidity
wind_chill_f
heat_index_f
pressure_in
pressure_mb
precipitation
precipitation_3hr
precipitation_6hr
""".strip().split("\n")


if __name__ == '__main__':

	# get database path
	db_path = 'weather.db'
	if len(sys.argv) > 1:
		db_path = sys.argv[1]
	if os.path.exists(db_path):
		print "Using database path: {}".format(db_path)
	else:
		sys.exit("Database file does not exist: {}".format(db_path))

	# run
	query_and_save(db_path, verbose=True)

