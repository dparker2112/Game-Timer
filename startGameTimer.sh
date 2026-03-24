#!/bin/bash
cd ~/dev/Game-Timer
# Activate virtual environment
source my-venv/bin/activate
# Run your Python script with sudo
XDG_RUNTIME_DIR=/run/user/$(id -u)
sudo env XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" PYTHONUNBUFFERED=1 my-venv/bin/python -u game_timer.py #> system_output.log