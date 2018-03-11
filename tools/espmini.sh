#!/bin/bash

HOST=192.168.4.1
PORT=3000

if [[ -z $2 ]]; then
    echo "Usage: ${0} put file ..."
    echo "       ${0} mkdir dir"
    exit
fi

if [[ $1 = put ]]; then
    shift
    for f in "$@"; do
	echo "put ${f} ..."
	{
	    echo "put"
	    echo $f
	    cat $f
	} | rpipe ${HOST}:${PORT}
    done
elif [[ $1 = mkdir ]]; then
    shift
    for f in "$@"; do
	echo "mkdir ${f} ..."
	{
	    echo "mkdir"
	    echo $f
	} | rpipe ${HOST}:${PORT}
    done
fi    
