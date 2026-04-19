#!/bin/bash

# Detect LAN IP on macOS
IP=$(ipconfig getifaddr en0)
if [ -z "$IP" ]; then
    IP=$(ipconfig getifaddr en1)
fi
if [ -z "$IP" ]; then
    IP="127.0.0.1"
fi

echo "🚀 Starting RoomPulse and opening browser to: https://$IP:5173"

# Open browser in the background after a 6-second delay to let Vite + Backend start
(sleep 6 && open "https://$IP:5173") &

# Export the IP so the backend Python container can read it and display the correct IP in the logs
export HOST_IP="$IP"

# Start the Docker containers
docker compose up --build
