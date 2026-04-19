from django.urls import path
from .views import DataView, control_crypto_stream

urlpatterns = [
    # .as_view() to return a callable view
    path("mqtt_data/", DataView.as_view(protocol="MQTT"), name="mqtt_data"),
    path("modbus_data/", DataView.as_view(protocol="MODBUS"), name="modbus_data"),
    path("control/<str:coin>/", control_crypto_stream, name="control_stream"),
]
