#!/bin/bash

function AMPY
{
    echo "$@ ..."
    ampy -b 115200 -p /dev/ttyS2 "$@"
}

AMPY mkdir boot
AMPY put boot.py
AMPY put boot/__init__.py boot/__init__.py
AMPY put boot/mini.py boot/mini.py
