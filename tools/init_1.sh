#!/bin/bash

espmini mkdir config data fonts lib service BOOT.FULL
espmini put boot/* config/*.py lib/*.py service/*.py

(
    cd ..
    espmini put data/* fonts/*
)

