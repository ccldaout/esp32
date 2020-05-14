#!/bin/bash

if [[ -z $1 ]]; then
    echo "Usage: $0 tty_device"
    exit 1
fi

TTY=/dev/${1}

function AMPY
{
    echo "$@ ..."
    ampy -b 115200 -p ${TTY} "$@"
}

AMPY mkdir boot
AMPY put boot.py
AMPY put boot/__init__.py boot/__init__.py
AMPY put boot/mini.py boot/mini.py
