import os
import sys
import json
import ssl
import paho.mqtt.client as mqtt
from pymongo import MongoClient

BROKER = os.environ.get("MQTT_BROKER", "localhost")
PORT = 8883
USERNAME = "crypto_publisher"
PASSWORD = "easycon26"
CA_CERTS = "certs/ca.crt"

MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "interview_db"
COLLECTION_NAME = "mqtt_data"

try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    collection = db[COLLECTION_NAME]
    mongo_client.admin.command("ping")  # Ping to be sure the db is running
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"CRITICAL ERROR: Could not connect to MongoDB. {e}")
    os._exit(1)


def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the Mosquitto broker."""
    if rc == 0:
        print("Successfully connected to secure MQTT broker.")
        topic = "data/crypto/#"  # Listens to every publisher topic
        client.subscribe(topic)
        print(f"Subscribed and listening for data on: {topic}")
    else:
        print(f"CRITICAL ERROR: Failed to connect to broker, return code {rc}")
        os._exit(1)


def on_message(client, userdata, msg):
    """Callback for when any data arrives from any publisher."""
    try:
        payload = json.loads(msg.payload.decode())  # Decode the JSON
        result = collection.insert_one(payload)

        print(f"Saved {payload.get('entity_id')} -> MongoID: {result.inserted_id}")

    except json.JSONDecodeError:
        print("Error: Received malformed JSON data.")
    except Exception as e:
        print(f"Database Error: Failed to insert document. {e}")


def main():
    client = mqtt.Client()

    # Security logic
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(ca_certs=CA_CERTS, tls_version=ssl.PROTOCOL_TLSv1_2)
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting from broker...")
        client.disconnect()
        print("Shutting dowm.")


if __name__ == "__main__":
    main()
