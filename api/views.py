from rest_framework.views import APIView
from rest_framework.response import Response
from .models import MetaData
from .mongo_utils import get_latest_data
import json
import ssl
import paho.mqtt.client as mqtt
from rest_framework.decorators import api_view


class DataView(APIView):
    protocol = None

    def get(self, request, *args, **kwargs):
        entities = MetaData.objects.filter(protocol=self.protocol)
        response_data = []

        if self.protocol == "MQTT":
            limit = 10
        else:
            limit = 20

        for entity in entities:
            entity_info = {
                "entity_id": entity.entity_id,
                "recent_data": get_latest_data(
                    entity.entity_id, entity.protocol, limit
                ),
            }
            response_data.append(entity_info)

        return Response(response_data)


BROKER = "localhost"
PORT = 8883
USERNAME = "crypto_publisher"
PASSWORD = "easycon26"

CA_CERTS = "/home/spuzikvadratnik/Easycon/interviewtask/mqtt_engine/certs/ca.crt"

ALLOWED_COINS = ["bitcoin", "ethereum", "litecoin", "dogecoin", "ripple"]


@api_view(["POST"])
def control_crypto_stream(request, coin):
    """Expects a POST request with a JSON body: {"action": "stop"} or {"action": "start"}"""

    if coin not in ALLOWED_COINS:
        return Response(
            {
                "error": f"Invalid coin. Must be exactly one of: {', '.join(ALLOWED_COINS)}"
            },
            status=400,
        )

    try:
        action = request.data.get("action")

        if action not in ["start", "stop"]:
            return Response(
                {"error": "Invalid action. Use 'start' or 'stop'."}, status=400
            )

        # Build a temporary MQTT client to publish the action
        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set(ca_certs=CA_CERTS, tls_version=ssl.PROTOCOL_TLSv1_2)
        client.tls_insecure_set(True)

        client.connect(BROKER, PORT, 60)

        topic = f"command/crypto/{coin}"
        payload = json.dumps({"action": action})

        client.publish(topic, payload)
        client.disconnect()  # Disconnect immediately after publish is done

        return Response({"message": f"Successfully sent '{action}' command to {coin}."})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
