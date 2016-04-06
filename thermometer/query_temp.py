#!/usr/bin/env python
import sys
import sqlite3
import ctypes, os

import temperusb

_sensor_count = 1  # Default unless specified otherwise
_sensor_id = [0,]  # Default to first sensor unless specified

def query_temp(admin_check=True):
	"""Returns a float of the temperature in fahrenheit
	"""
	# check that running as admin
	if admin_check:
		try:
			is_admin = os.getuid() == 0
		except AttributeError:
			is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
		if not is_admin:
			raise SystemError("Must run as administrator")

	# get device
	th = temperusb.TemperHandler()
	devs = th.get_devices()
	if len(devs) > 1:
		ValueError('More than one device found')
	dev = devs[0]

	# query device
	dev.set_sensor_count(_sensor_count)
	reading = dev.get_temperatures(sensors=_sensor_id)
	if len(reading) > 1:
		ValueError('More than one set of data in reading')

	# parse result
	reading_data = reading.itervalues().next()
	fahrenheit = reading_data['temperature_f']
	return fahrenheit

def database_setup(db_path):
	"""Creates a sqlite database with a temperature table
	"""
	db = sqlite3.connect(db_path)

	sql = """
	CREATE TABLE temp(
		id INTEGER PRIMARY KEY,
		read_time DATETIME DEFAULT (datetime('now', 'localtime')),
		temperature FLOAT)
	"""
	db.execute("DROP TABLE IF EXISTS temp")
	db.execute(sql)
	db.commit()
	return db

def database_connect(db_path="therm.db"):
	db = sqlite3.connect(db_path)
	return db

def database_insert(db, temperature):
	"""Record a value in the databse"""
	curs = db.cursor()
	curs.execute("INSERT INTO temp(temperature) VALUES(?)", (temperature,))
	db.commit()
	id = curs.lastrowid
	return curs.execute("SELECT * FROM temp WHERE id=?", (id,)).fetchone()

def database_select(db):
	rows = db.execute("SELECT * FROM temp")
	return rows

def query_and_record(db):
	temp = query_temp()
	return database_insert(db, temp)

if __name__ == '__main__':
	# without arguments
	if len(sys.argv) == 1:
		try:
			print "{:2.1f}".format(query_temp())
		except SystemError as e:
			sys.exit(str(e))
	else:
		subcommand = sys.argv[1]
		if subcommand == "db":
			if len(sys.argv) >= 3:
				db_path = sys.argv[2]
				if not os.path.exists(db_path):
					sys.exit("Database path does not exist: {}".format(db_path))
				db = database_connect(db_path)
			else:
				db = database_connect()
			res = query_and_record(db)
			print res
			sys.exit()
		elif subcommand == "get":
			db = database_connect()
			rows = database_select(db)
			for row in rows:
				print row
		else:
			sys.exit("Usage: {} [db [db_path]]").format(sys.argv[0])


