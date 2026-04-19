from pymongo import MongoClient

client = MongoClient("mongodb://mongodb:27017/")  # default port for MongoDB
db = client["interview_db"]


def get_latest_data(entity_id, protocol, limit):
    if protocol == "MQTT":
        collection = db["mqtt_data"]
    else:
        collection = db["modbus_data"]

    data = list(
        collection.find(
            {"entity_id": entity_id}, {"_id": 0, "entity_id": 0}  # unnecessary data
        )
        .sort("timestamp", -1)
        .limit(limit)
    )

    return data
