#!/usr/bin/python

import cherrypy
import datetime
import dateutil.parser
import json
import logging
import os.path
import sqlite3
import sys
import time

from mako.template import Template
from mako.lookup import TemplateLookup

OUTER_TEMPERATURE_ADJUSTMENT = 0
INNER_TEMPERATURE_ADJUSTMENT = 0

MIN_IN_MILLIS = 60 * 1000
HOUR_IN_MILLIS = MIN_IN_MILLIS * 60
DAY_IN_MILLIS = HOUR_IN_MILLIS * 24
WEEK_IN_MILLIS = DAY_IN_MILLIS * 7

def RoundToSingleDecimal(number):
  return int(number * 10 + 0.5) / 10.0

def CurrentMillis():
  return int(time.time() * 1000)

def StrDateTimeToMillis(strDateTime):
    datetime_object = dateutil.parser.parse(strDateTime)
    return 1000 * int(datetime_object.strftime('%s'))

def MillisToStrDateTime(millis):
  date = datetime.datetime.fromtimestamp(int(millis / 1000))
  return date.strftime('%Y-%m-%d %H:%M')

def FloorMillisToNearestMin(millis):
  return int(int(millis) / 60000) * 60000


class ServerRoot(object):
  def __init__(self):
    self._log = logging.getLogger("ServerRoot")
    self._db = "temper.sqlite3"
    self._InitDb()

  def _DbConnection(self):
    return sqlite3.connect(self._db)

  def _InitDb(self):
    db = self._DbConnection()
    cursor = db.cursor()
    sql = 'CREATE TABLE IF NOT EXISTS temper_table (id INTEGER PRIMARY KEY, timestamp INTEGER, inner_temperature REAL, outer_temperature REAL)'
    cursor.execute(sql)
    db.commit()

  def _InsertIntoDb(self, timestamp, inner_temperature, outer_temperature):
    db = self._DbConnection()
    cursor = db.cursor()
    sql = 'INSERT INTO temper_table(timestamp, inner_temperature, outer_temperature) VALUES(%d, %f, %f)' % (timestamp, inner_temperature, outer_temperature)
    cursor.execute(sql)
    db.commit()

  def _SelectFromDb(self, sql):
    db = self._DbConnection()
    cursor = db.cursor()
    cursor.execute(sql)
    column_names = [d[0] for d in cursor.description]
    result = []
    for row in cursor:
      info = dict(zip(column_names, row))
      result.append(info)
    return result

  def _ComputeBucketMillis(self, start_millis, last_millis):
    delta_millis = last_millis - start_millis
    if delta_millis <= HOUR_IN_MILLIS:
      return MIN_IN_MILLIS
    elif delta_millis <= 6 * HOUR_IN_MILLIS:
      return 5 * MIN_IN_MILLIS
    elif delta_millis <= DAY_IN_MILLIS:
      return 15 * MIN_IN_MILLIS
    elif delta_millis <= WEEK_IN_MILLIS:
      return HOUR_IN_MILLIS
    elif delta_millis <= 31 * DAY_IN_MILLIS:
      return 6 * HOUR_IN_MILLIS
    else:
      return DAY_IN_MILLIS

  def _SelectRangeFromDb(self, start_millis, last_millis):
    bucket_millis = self._ComputeBucketMillis(start_millis, last_millis)
    sql = """
      SELECT
        CAST(1 + (timestamp / %(bucket_millis)d) AS INTEGER) * %(bucket_millis)d AS ctimestamp,
        SUM(inner_temperature) / COUNT(*) AS cinner_temperature,
        SUM(outer_temperature) / COUNT(*) AS couter_temperature
      FROM temper_table
      WHERE timestamp <= %(last_millis)d and timestamp >= %(start_millis)d
      GROUP BY CAST(timestamp / %(bucket_millis)d AS INTEGER)
      ORDER BY timestamp;
    """ % { "bucket_millis":bucket_millis, "start_millis":start_millis, "last_millis":last_millis }
    return self._SelectFromDb(sql)

  def _HandleGet(self, args):
    mytemplate = Template(filename='get.mako.html')
    if "refresh" in args and args["refresh"] == "true":
      refresh = True
    else:
      refresh = False
    if "last_datetime" in args:
      last_datetime = args["last_datetime"]
      last_millis = StrDateTimeToMillis(last_datetime)
    else:
      last_millis = CurrentMillis()
      last_datetime = MillisToStrDateTime(last_millis)
    data = { "refresh":refresh, "last_datetime":last_datetime, "last_millis":last_millis }
    return mytemplate.render(**data)

  def _HandlePost(self):
    cl = cherrypy.request.headers['Content-Length']
    rawbody = cherrypy.request.body.read(int(cl))
    body = rawbody.decode("utf-8")
    splits = body.split(";")
    inner = float(splits[1].split(" ")[0])
    outer = float(splits[2].split(" ")[0])
    timestamp = CurrentMillis()
    self._InsertIntoDb(timestamp, inner, outer)
    return "This is a POST and the body was: " + body

  @cherrypy.expose
  def index(self, **args):
    request = cherrypy.request
    method = request.method.upper()
    if method == "POST":
      return self._HandlePost()
    elif method == "GET":
      return self._HandleGet(args)
    raise cherrypy.HTTPError(404)

  @cherrypy.expose
  def json(self, **args):
    if not "start_millis" in args:
      raise cherrypy.HTTPError(400)
    if not "last_millis" in args:
      raise cherrypy.HTTPError(400)
    last_millis = FloorMillisToNearestMin(args["last_millis"])
    start_millis = FloorMillisToNearestMin(args["start_millis"])
    rows = self._SelectRangeFromDb(start_millis, last_millis)
    MAX_POINTS = 100
    assert len(rows) <= MAX_POINTS
    inner = []
    outer = []
    labels = []
    for i in range(len(rows)):
      row = rows[i]
      outer.append(RoundToSingleDecimal(
          row["couter_temperature"] + OUTER_TEMPERATURE_ADJUSTMENT))
      inner.append(RoundToSingleDecimal(
          row["cinner_temperature"] + INNER_TEMPERATURE_ADJUSTMENT))
      labels.append(MillisToStrDateTime(row["ctimestamp"]))
      print("rui {}-{}:{}".format(i, labels[-1], outer[-1]))
    data = {
      "labels":labels,
      "datasets":(
      {
        'label': 'House Temperature',
        'fill': 'bottom',
        'backgroundColor': 'rgba(0, 255, 0, 0.1)',
        'borderColor': 'rgba(0, 255, 0, 1)',
        'borderWidth': '1',
        'data' : outer,
    },)}
    return json.dumps(data)


def Main(argv):
  cherrypy.config.update({
      "server.socket_port" : 4284,
      "server.socket_host" : "0.0.0.0"})

  cherrypy.quickstart(ServerRoot(), config={
    '/static': {
      'tools.staticdir.on':True,
      'tools.staticdir.dir':os.path.abspath("static")
    }})


if __name__ == "__main__":
  Main(sys.argv)
