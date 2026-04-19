from django.db import models


class MetaData(models.Model):
    protocol_choices = [
        ("MQTT", "MQTT"),
        ("MODBUS", "Modbus TCP"),
    ]

    entity_id = models.CharField(max_length=100, unique=True)
    protocol = models.CharField(max_length=15, choices=protocol_choices)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entity_id} ({self.protocol})"
