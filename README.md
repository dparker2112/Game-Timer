# Game-Timer

logging notes:
journalctl -f -t game_timer              # Follow logs
journalctl -t game_timer --since '1 hour ago'  # Last hour
journalctl -t game_timer -p err          # Errors only