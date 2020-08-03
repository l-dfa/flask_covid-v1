#!/bin/bash
# getting data from ecdc

DDIR=/usr/share/nginx/html/flask_covid/instance/data/
DFILE=covid19-worldwide.csv
DLOG=covid19-worldwide.log
TODAY=$(date +"%Y-%m-%d")
OLDFILE=covid19-worldwide-${TODAY}.csv
#HDIR=/root
#RESTARTSH=restart_covid.sh

mv $DDIR$DFILE $DDIR$OLDFILE

if ! wget https://opendata.ecdc.europa.eu/covid19/casedistribution/csv -O $DDIR$DFILE -o $DDIR$DLOG; then
    mv $DIR$OLDFILE $DIR$FILE 
    echo error: rollback to old data file >> $DDIR$DLOG
    exit
fi

#source $HDIR$RESTARTSH
