import time
import threading
import requests
from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)

# We create 3 registers, one for temperature, windspeed and humidity
store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0] * 3), zero_mode=True)
context = ModbusServerContext(slaves=store, single=True)


def update_weather_data():
    """This background thread fetches data from the Prague
    every 10 minutes and updates the Modbus registers.
    """

    # We request temperature, wind speed and humidity
    url = "https://api.open-meteo.com/v1/forecast?latitude=50.0880&longitude=14.4208&current=temperature_2m,relative_humidity_2m,wind_speed_10m"

    while True:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            temp = data["current"]["temperature_2m"]
            wind = data["current"]["wind_speed_10m"]
            humidity = data["current"]["relative_humidity_2m"]

            # Cover for floating point data
            temp_scaled = int(temp * 10)
            wind_scaled = int(wind * 10)
            humidity_scaled = int(humidity * 10)

            # Handle negative temperatures using 16-bit two's complement
            if temp_scaled < 0:
                temp_scaled = (temp_scaled + 65536) & 0xFFFF

            context[0].setValues(3, 0, [temp_scaled, wind_scaled, humidity_scaled])

            print(
                f"[API UPDATE] Temp: {temp}°C, Wind: {wind}km/h, Humidity: {humidity}%"
            )

        except Exception as e:
            print(f"[ERROR] Failed to fetch weather data: {e}")

        # 10 minutes since weather rarely changes from minute to minute
        time.sleep(600)


def run_modbus_server():
    """Runs the Modbus TCP server on port 5020.
    We use 5020 instead of the standard 502 so we don't need root/sudo privileges.
    """

    print("Starting Modbus TCP Server on localhost:5020...")
    # address=("127.0.0.1", 5020) to bind only to localhost
    StartTcpServer(context=context, address=("127.0.0.1", 5020))


if __name__ == "__main__":
    # Background thread so that the client can read the registers
    # even if update_weather_data is sleeping
    api_thread = threading.Thread(target=update_weather_data, daemon=True)
    api_thread.start()

    run_modbus_server()
