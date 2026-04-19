#!/bin/bash

echo "Starting MQTT Engine..."

cd mqtt_engine || { echo "Directory 'mqtt_engine' not found."; exit 1; }

PIDS=()

trap 'echo -e "\nShutting down all MQTT services..."; kill "${PIDS[@]}" 2>/dev/null; exit 0' SIGINT SIGTERM

python3 mongo_subscriber.py &
PIDS+=($!)
echo "[STARTED] MongoDB Subscriber"

COINS=("bitcoin" "ethereum" "litecoin" "dogecoin" "ripple")

for COIN in "${COINS[@]}"; do
    python3 coingecko_publisher.py "$COIN" &
    PIDS+=($!)
    echo "[STARTED] $COIN Publisher"
    sleep 20
done

echo "-------------------------------------------------"
echo "All MQTT services are running."
echo "Press Ctrl+C to stop all services."
echo "-------------------------------------------------"

wait
