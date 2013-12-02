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

OUTER_TEMPERATURE_ADJUSTMENT = 2.50
INNER_TEMPERATURE_ADJUSTMENT = -8.00

def CurrentMillis():
  return int(time.time() * 1000)


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

  def _SelectBucketsFromDb(self, bucket_millis, last_millis):
    sql = """
      SELECT
        CAST(timestamp / %(bucket_millis)s AS INTEGER) * %(bucket_millis)s AS ctimestamp,
        SUM(inner_temperature) / COUNT(*) AS cinner_temperature,
        SUM(outer_temperature) / COUNT(*) AS couter_temperature
      FROM temper_table
      WHERE timestamp <= %(last_millis)s
      GROUP BY CAST(timestamp / %(bucket_millis)s AS INTEGER)
      ORDER BY timestamp
      DESC LIMIT 42;
    """ % { "bucket_millis":bucket_millis, "last_millis":last_millis }
    return self._SelectFromDb(sql)

  def _HandleGet(self, args):
    mytemplate = Template(filename='get.mako.html')
    if "refresh" in args and args["refresh"] == "true":
      refresh = True
    else:
      refresh = False
    if "last_datetime" in args:
      last_datetime = args["last_datetime"]
    else:
      last_datetime = str(datetime.datetime.fromtimestamp(CurrentMillis() / 1000))
    data = { "refresh":refresh, "last_datetime":last_datetime }
    return mytemplate.render(**data)

  def _HandlePost(self):
    cl = cherrypy.request.headers['Content-Length']
    rawbody = cherrypy.request.body.read(int(cl))
    body = rawbody.decode("utf-8")
    splits = body.split(";")
    inner = float(splits[1].split(" ")[0])
    outer = float(splits[2].split(" ")[0])
    timestamp = CurrentMillis()
    print "timestamp=%d inner=%f outer=%f" % (timestamp, inner, outer)
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
    if not "bucket_millis" in args:
      raise cherrypy.HTTPError(400)
    last_datetime = datetime.datetime.fromtimestamp(CurrentMillis() / 1000)
    if "last_datetime" in args:
      try:
        last_datetime = dateutil.parser.parse(args["last_datetime"])
      except:
        self._log.error("Failed to parse date: " + args["last_datetime"])
    last_millis = 1000 * int(last_datetime.strftime('%s'))
    bucket_millis = args["bucket_millis"]
    rows = self._SelectBucketsFromDb(bucket_millis, last_millis)
    inner = []
    outer = []
    labels = []
    for i in range(len(rows) - 1, -1, -1):
      row = rows[i]
      outer.append(row["couter_temperature"] + OUTER_TEMPERATURE_ADJUSTMENT)
      inner.append(row["cinner_temperature"] + INNER_TEMPERATURE_ADJUSTMENT)
      labels.append(str(datetime.datetime.fromtimestamp(row["ctimestamp"] / 1000)))
    data = {
      "labels":labels,
      "datasets":({
        'fillColor' : "rgba(220,220,220,0.5)",
        'strokeColor' : "rgba(220,220,220,1)",
        'pointColor' : "rgba(220,220,220,1)",
        "pointStrokeColor":"#fff",
        "data" : inner
      }, {
        'fillColor' : "rgba(151,187,205,0.5)",
        'strokeColor' : "rgba(151,187,205,1)",
        'pointColor' : "rgba(151,187,205,1)",
        'pointStrokeColor' : "#fff",
        'data' : outer
    })}
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
