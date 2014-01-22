#!/bin/sh
# Starts and stops temperpi.server 

TEMPERPI_SERVER_PATH=/home/ruibm/git/temperpi/server
MAIN=main.py
PIDFILE=$MAIN.pid

cd $TEMPERPI_SERVER_PATH

case "$1" in
  start)
    if [ -f $PIDFILE ] ; then
      $0 stop
    fi
    python $MAIN > /dev/null 2>&1 & 
    PID=$!
    echo "$PID" > $PIDFILE
    echo "Successfully started running [$0] with pid [$PID]."
    ;;

  stop)
    if [ -f $PIDFILE ] ; then
      PID=`cat $PIDFILE`
      kill -KILL $PID
      rm $PIDFILE
      echo "Successfully killed [$0] with pid [$PID]."
    else
      $0 status
    fi

    ;;

  restart)
    $0 stop
    $0 start
    ;;

  status)
    if [ -f $PIDFILE ] ; then
      PID=`cat $PIDFILE`
      echo "[$0] is running with pid [$PID]."
      ps -p $PID
      exit 0
    else
      echo "[$0] is not running."
      exit 1
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac

