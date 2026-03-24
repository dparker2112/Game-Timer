#!/bin/bash

# Clear persistent game data
# Use this script to manually revert to default audio

echo "Clearing persistent game data..."

# Remove the temp directory containing loaded game
if [ -d "temp" ]; then
    echo "Removing temp directory..."
    rm -rf temp
    echo "✓ temp directory removed"
else
    echo "No temp directory found"
fi

# Clear any game state files
if [ -f ".game_loaded" ]; then
    echo "Removing game state file..."
    rm -f .game_loaded
    echo "✓ game state file removed"
fi

echo ""
echo "Persistent game data cleared."
echo "Next time the game timer starts, it will use default audio."
echo ""
echo "To load a new game, insert a USB drive with game files."
