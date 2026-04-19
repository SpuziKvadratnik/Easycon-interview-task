from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from .models import MetaData


class DataViewAPITests(APITestCase):

    def setUp(self):
        self.mqtt_entity = MetaData.objects.create(entity_id="bitcoin", protocol="MQTT")
        self.modbus_entity = MetaData.objects.create(
            entity_id="prague_weather", protocol="MODBUS"
        )

    @patch("api.views.get_latest_data")
    def test_get_mqtt_data(self, mock_get_latest_data):
        """Test GET request for MQTT data, ensuring limit is 10"""

        mock_get_latest_data.return_value = [
            {"price": 65000, "timestamp": "2026-04-06T23:00:00"}
        ]

        url = reverse("mqtt_data")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["entity_id"], "bitcoin")
        self.assertEqual(response.data[0]["recent_data"][0]["price"], 65000)

        mock_get_latest_data.assert_called_once_with("bitcoin", "MQTT", 10)

    @patch("api.views.get_latest_data")
    def test_get_modbus_data(self, mock_get_latest_data):
        """Test GET request for MODBUS data, ensuring limit is 20"""

        mock_get_latest_data.return_value = [
            {"temp": 15.5, "timestamp": "2026-04-06T23:00:00"}
        ]

        url = reverse("modbus_data")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["entity_id"], "prague_weather")
        self.assertEqual(response.data[0]["recent_data"][0]["temp"], 15.5)

        mock_get_latest_data.assert_called_once_with("prague_weather", "MODBUS", 20)


class CryptoControlAPITests(APITestCase):

    def setUp(self):
        self.entity = MetaData.objects.create(entity_id="bitcoin", protocol="MQTT")

    @patch("paho.mqtt.client.Client.publish")
    def test_control_crypto_stop(self, mock_publish):
        """Test Sending a 'stop' action via POST"""

        url = reverse("control_stream", kwargs={"coin": "bitcoin"})

        data = {"action": "stop"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Successfully sent 'stop' command to bitcoin."
        )
        mock_publish.assert_called_once()

    @patch("paho.mqtt.client.Client.publish")
    def test_control_crypto_start(self, mock_publish):
        """Test Sending a 'start' action via POST"""

        url = reverse("control_stream", kwargs={"coin": "bitcoin"})
        data = {"action": "start"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Successfully sent 'start' command to bitcoin."
        )
        mock_publish.assert_called_once()

    def test_invalid_coin_rejection(self):
        """Test that the API correctly rejects coins not in ALLOWED_COINS"""

        url = reverse("control_stream", kwargs={"coin": "made_up_coin"})
        data = {"action": "start"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid coin", response.data["error"])
