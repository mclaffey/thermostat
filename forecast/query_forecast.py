#!/usr/bin/env python

import urllib2
import json
import sqlite3
import datetime
import sys, os

forecast_api_url="http://api.wunderground.com/api/9836d881af5d6fc2/hourly/q/NC/Charlotte.json"

def query_and_save(db_path, verbose=False):
	db = sqlite3.connect(db_path)
	forecast_tuples = query_forecast(verbose)
	append_records(db, forecast_tuples)

def setup_database(db):
	# setup table and index
	sql = """
	CREATE TABLE forecasts(
	  create_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
	  is_latest BOOLEAN default(1),
	  forecast_datetime DATETIME,
	  temperature NUMERIC)
	"""
	db.execute("DROP TABLE IF EXISTS forecasts")
	db.execute(sql)

	db.execute("DROP INDEX IF EXISTS forecast_unique")
	db.execute("CREATE UNIQUE INDEX forecast_unique ON forecasts(create_datetime, forecast_datetime)")
	db.commit()	

def append_records(db, forecast_tuples):
	"""Add records to the setup_database

	forecast_tuples is a list of tuples in the form: [(datetime, temp), (datetime, temp), ...]
	"""
	# clear is_latest flags
	db.execute("UPDATE forecasts SET is_latest=0")
	db.executemany("INSERT INTO forecasts(forecast_datetime, temperature) VALUES(?, ?)", forecast_tuples)
	db.commit()

def get_latest_records(db):
	"""Provide a generator for the latest records in the form of forecast_tuples

	Each yield is a tuples in the form: (u'datetime, temp)
	"""
	rows = db.execute("SELECT forecast_datetime, temperature FROM forecasts WHERE is_latest=1 ORDER BY forecast_datetime")
	for row in rows:
	    yield (row[0], row[1])

def query_forecast(verbose=False):
	"""Query weather.com API for hourly forecast
	"""
	if verbose:
		print "Querying weather.com for forecase...",
		sys.stdout.flush()
	f = urllib2.urlopen(forecast_api_url)
	json_string = f.read()
	f.close()
	if verbose:
		print "Done"
		sys.stdout.flush()
	parsed_json = json.loads(json_string)
	forecast_list = parsed_json['hourly_forecast']
	forecast_tuples = [(datetime.datetime.strptime(forecast['FCTTIME']['pretty'], '%I:%M %p %Z on %B %d, %Y'),
	                    int(forecast['temp']['english']))
	                   for forecast in forecast_list]
	return forecast_tuples

if __name__ == '__main__':
	db_path = "forecast.db"
	if len(sys.argv) > 0:
		db_path = sys.argv[1]
	if os.path.exists(db_path):
		print "Using database: {}".format(db_path)
	else:
		sys.exit("Database does not exist: {}".format(db_path))
	query_and_save(db_path, verbose=True)

