#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

while true
do
   rm -f $1
   $SCRIPT_DIR/jabberhive-two-way-replace.py -s $1 -d $2
   sleep 60
done
