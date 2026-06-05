#!/bin/bash

# Game Timer Deployment Script
# Syncs the local repo to a Raspberry Pi over the network
#
# Usage: ./deploy_to_pi.sh [PI_IP_ADDRESS]
#   If no IP is provided, will use the default below

# Configuration - EDIT THESE VALUES
PI_USER="gameTimerUser"                    # Username on Pi
PI_PATH="/home/gameTimerUser/dev/Game-Timer"   # Destination path on Pi
LOCAL_PATH="$(pwd)"             # Current directory (should be repo root)

# Get IP from command line or use default
if [ $# -eq 0 ]; then
    PI_HOST="192.168.1.100"     # Default IP address
    echo -e "${YELLOW}No IP provided, using default: ${PI_HOST}${NC}"
else
    PI_HOST="$1"
    echo -e "${YELLOW}Using provided IP: ${PI_HOST}${NC}"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Game Timer Deployment Script${NC}"
echo "=================================="

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    echo "Please run this script from the repo root directory"
    exit 1
fi

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Error: rsync not found${NC}"
    echo "Please install rsync: brew install rsync (macOS) or apt-get install rsync"
    exit 1
fi

# Test connectivity to Pi
echo -e "${YELLOW}Testing connectivity to ${PI_HOST}...${NC}"
if ! ping -c 1 "$PI_HOST" &> /dev/null; then
    echo -e "${RED}Error: Cannot reach ${PI_HOST}${NC}"
    echo "Please check the IP address and network connectivity"
    exit 1
fi

# Show current git status
echo -e "${YELLOW}Current git status:${NC}"
git status --porcelain
echo ""

# Ask for confirmation
echo -e "${YELLOW}About to sync:${NC}"
echo "  From: $LOCAL_PATH"
echo "  To:   ${PI_USER}@${PI_HOST}:${PI_PATH}"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Create destination directory and set permissions in one SSH call
echo -e "${YELLOW}Creating destination directory on Pi...${NC}"
ssh "${PI_USER}@${PI_HOST}" "mkdir -p ${PI_PATH} && chmod +x ${PI_PATH}/*.py 2>/dev/null || true"

# Sync files using rsync
echo -e "${YELLOW}Syncing files to Pi...${NC}"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/*' \
    --exclude='temp/*' \
    --exclude='.DS_Store' \
    --exclude='*.tmp' \
    "${LOCAL_PATH}/" \
    "${PI_USER}@${PI_HOST}:${PI_PATH}/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Sync completed successfully${NC}"
else
    echo -e "${RED}✗ Sync failed${NC}"
    exit 1
fi

# Show deployed files
echo -e "${YELLOW}Deployed files on Pi:${NC}"
ssh "${PI_USER}@${PI_HOST}" "ls -la ${PI_PATH}/"

echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "To run the game timer on the Pi:"
echo "  ssh ${PI_USER}@${PI_HOST}"
echo "  cd ${PI_PATH}"
echo "  python3 game_timer.py"
