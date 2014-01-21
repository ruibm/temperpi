#!/bin/sh
# Starts and stops temperpi.server 

TEMPERPI_SERVER_PATH=/Users/rui/git/temperpi/server
MAIN=main.py
PIDFILE=$MAIN.pid

cd $TEMPERPI_SERVER_PATH

case "$1" in
  start)
    if [ -f $PIDFILE ] ; then
      $0 stop
    fi
    python $MAIN &> /dev/null &
    PID=$!
    echo "$PID" > $PIDFILE
    echo "Successfully started running [$0] with pid [$PID]."
    ;;

  stop)
    PID=`cat $PIDFILE`
    kill -KILL $PID
    rm $PIDFILE
    echo "Successfully killed [$0] with pid [$PID]."

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
      echo "[$0] is not running"
      exit 1
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac

