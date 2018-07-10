#!/bin/bash

if [[ "$#" -ne 1 ]]; then
  echo "Usage: ./send.sh [SERVER_URL]"
  echo "  SERVER_URL - The url of the server receiving the data."
  exit 42
fi

SERVER_URL="$1"

wget \
  --post-data "`sudo ./TEMPer2/temper`" \
  --header="Content-Type:text/plain" \
  --output-document index.html \
  ${SERVER_URL} \
  && cat index.html \
  && rm index.html
