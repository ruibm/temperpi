#!/bin/bash

if [[ "$#" -ne 1 ]]; then
  echo "Usage: ./send.sh [SERVER_URL]"
  echo "  SERVER_URL - The url of the server receiving the data."
  exit 42
fi

SERVER_URL="$1"
INDEX_FILE='/tmp/temperpi.index.html'
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

wget \
  --post-data "`sudo ${SCRIPTPATH}/TEMPer2/temper`" \
  --header="Content-Type:text/plain" \
  --output-document ${INDEX_FILE} \
  ${SERVER_URL} \
  && cat ${INDEX_FILE} \
  && rm ${INDEX_FILE}
exit $?
