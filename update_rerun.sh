#!/bin/bash

pkill -f main.py
nohup python3 main.py > output.log &
cat output.log