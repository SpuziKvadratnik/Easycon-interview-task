#!/bin/bash

PIDS=()

cleanup() {
    echo -e "\n[SYSTEM] Shutting down all Modbus services..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "[1/3] Starting Modbus Python Server..."
python3 ./modbus_engine/weather_server.py &
PIDS+=($!)
sleep 5

echo "[2/3] Starting Stunnel Bouncer..."
stunnel ./modbus_engine/stunnel.conf &
PIDS+=($!)
sleep 5

echo "[3/3] Starting Modbus Poller Client..."
echo "--------------------------------------------------"
python3 ./modbus_engine/weather_client.py

cleanup
