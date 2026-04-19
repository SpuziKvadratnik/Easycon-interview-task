import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymongo import MongoClient

MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "interview_db"
COLLECTION_NAME = "modbus_data"

try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    collection = db[COLLECTION_NAME]
    mongo_client.admin.command("ping")  # Ping to be sure the db is running
    print("Successfully connected to MongoDB.")
except Exception as e:
    print(f"CRITICAL ERROR: Could not connect to MongoDB. {e}")
    os._exit(1)

modbus_client = ModbusTcpClient("127.0.0.1", port=6000)


def decode_temperature(raw_value):
    """Applies the 'Decoder Ring' for Two's Complement negative numbers."""

    if raw_value > 32767:
        raw_value -= 65536
    return raw_value / 10.0


def sane_data(temp, wind, humidity):
    """Prevents poisoned, malicious, or glitched data from entering the database."""

    if not (-50.0 <= temp <= 60.0):
        print(
            f"[SECURITY ALERT] Temperature {temp}°C out of realistic bounds! Dropping payload."
        )
        return False
    if not (0.0 <= wind <= 300.0):
        print(
            f"[SECURITY ALERT] Wind {wind}km/h out of realistic bounds! Dropping payload."
        )
        return False
    if not (0.0 <= humidity <= 100.0):
        print(f"[SECURITY ALERT] Humidity {humidity}% out of bounds! Dropping payload.")
        return False
    return True


def run_poller():
    print("Starting Modbus Poller. Attempting to connect to Server...")

    if not modbus_client.connect():
        print("[ERROR] Cannot connect to Modbus Server. Is it running?")
        return

    print("Connected! Polling every 5 seconds...")

    try:
        while True:
            result = modbus_client.read_holding_registers(address=0, count=3, slave=1)

            if result.isError():
                print("[ERROR] Failed to read registers.")
            else:
                raw_temp = result.registers[0]
                raw_wind = result.registers[1]
                raw_humidity = result.registers[2]

                temp_c = decode_temperature(raw_temp)
                wind_kph = raw_wind / 10.0
                humidity_pct = raw_humidity / 10.0

                print(
                    f"[POLL SUCCESS] Raw Regs: {result.registers} -> Decoded: Temp: {temp_c}°C, Wind: {wind_kph}km/h, Hum: {humidity_pct}%"
                )

                if sane_data(temp_c, wind_kph, humidity_pct):

                    payload = {
                        "entity_id": "Prague_weather",
                        "temperature_c": temp_c,
                        "wind_speed_kph": wind_kph,
                        "humidity_pct": humidity_pct,
                        "timestamp": datetime.utcnow(),
                    }

                    inserted_id = collection.insert_one(payload).inserted_id
                    print(f"   -> [DATABASE] Inserted record with ID: {inserted_id}")

            # 5 seconds seems to be in the most common frequency range
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nStopping Poller...")
    finally:
        modbus_client.close()
        mongo_client.close()


if __name__ == "__main__":
    run_poller()
