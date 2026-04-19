import sys
import time
import json
import requests
import paho.mqtt.client as mqtt
import ssl
import random

BROKER = os.environ.get("MQTT_BROKER", "localhost")
PORT = 8883
USERNAME = "crypto_publisher"
PASSWORD = "easycon26"
CA_CERTS = "certs/ca.crt"

is_paused = False  # Track if paused from REST API


def on_connect(client, userdata, flags, rc):
    """Callback for when the client securely connects to the broker."""

    if rc == 0:
        print(f"[{userdata['coin']}] Successfully connected to secure broker.")
        # Listen for stop/run commands
        command_topic = f"command/crypto/{userdata['coin']}"
        client.subscribe(command_topic)
        print(f"[{userdata['coin']}] Listening for commands on: {command_topic}")
    else:
        print(f"Failed to connect, return code {rc}")
        os._exit(1)


def on_message(client, userdata, msg):
    """Callback for when a message arrives on the command topic."""

    global is_paused
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")

        if action == "stop":
            print(f"\n--- COMMAND RECEIVED: Pausing {userdata['coin']} stream ---")
            is_paused = True
        elif action == "start":
            print(f"\n--- COMMAND RECEIVED: Resuming {userdata['coin']} stream ---")
            is_paused = False
    except json.JSONDecodeError:
        print("Received invalid command format.")


def main():
    global is_paused

    # Ensure the user provided a coin name
    if len(sys.argv) < 2:
        print("Usage: python3 coincap_publisher.py <coin_id>")
        print("Example: python3 coincap_publisher.py bitcoin")
        sys.exit(1)

    coin = sys.argv[1].lower()

    client = mqtt.Client(userdata={"coin": coin})

    # Security logic
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(ca_certs=CA_CERTS, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.tls_insecure_set(True)  # Required when using 'localhost' self-signed certs

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    while True:
        if not is_paused:
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=eur"
                response = requests.get(url)
                response.raise_for_status()

                raw_data = response.json()
                price = float(raw_data[coin]["eur"])

                # entity_id to match the PostgreSQL model
                payload = {
                    "entity_id": f"{coin.capitalize()}_Stream",
                    "price": price,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }

                publish_topic = f"data/crypto/{coin}"
                client.publish(publish_topic, json.dumps(payload))
                print(f"[{coin}] Published: ${payload['price']:.2f}")

            except requests.exceptions.RequestException as e:
                print(f"[{coin}] API Error: {e}")
            except KeyError as e:
                print(f"[{coin}] Data parsing error (Unexpected JSON): {e}")

        # There are 5 clients, each initiated 20 seconds after the
        # previous one. 120 second sleep ensures that there is a
        # request every 20 seconds, satisfying the limit of coingecko
        time.sleep(120)


if __name__ == "__main__":
    main()
