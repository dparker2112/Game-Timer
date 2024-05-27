#!/bin/bash
cd ~/dev/Game-Timer
# Activate virtual environment
source my-venv/bin/activate
# Run your Python script with sudo
sudo my-venv/bin/python game_timer.py #> system_output.log