#!/bin/bash

# Install systemd-python package for journalctl logging
# Run this on the Raspberry Pi to enable journalctl logging

echo "Installing systemd-python for journalctl logging support..."

# Update package lists
sudo apt-get update

# Install systemd-python (provides systemd.journal module)
sudo apt-get install -y systemd-python

# Alternative for newer systems
sudo apt-get install -y python3-systemd

echo "Installation complete!"
echo ""
echo "You can now use journalctl logging by setting LOGGING_MODE = 'journalctl' in game_timer.py"
echo ""
echo "View logs with:"
echo "  journalctl -f -t game_timer"
echo "  journalctl -t game_timer --since '1 hour ago'"
echo "  journalctl -t game_timer -p err"
