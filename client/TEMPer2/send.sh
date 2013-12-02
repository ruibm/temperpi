#!/bin/bash

while [ 1 ]
do
  TEMPERPI=http://192.168.0.7:4284
  wget --post-data "`sudo ./TEMPer2/temper`"  --header="Content-Type:text/plain" --output-document index.html ${TEMPERPI}  && cat index.html
  sleep 1
done
