from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.core import Device


def test_device_schema_valid():
    d = Device(
        chip_mac="AA:BB:CC:DD:EE:FF",
        node_type="sensor_node",
        room_id=1,
        building="Main",
        floor="1",
        room="101",
        label="Temp Sensor 1",
        x=10,
        y=20,
        capabilities=["temperature", "humidity"],
        payload_encoder_key="temp_v1",
        uplink_interval_seconds=60,
        firmware_version="1.0.0",
    )
    assert d.chip_mac == "AA:BB:CC:DD:EE:FF"
    assert d.node_type == "sensor_node"
    assert d.room_id == 1
    assert d.capabilities == ["temperature", "humidity"]


def test_device_schema_minimal():
    d = Device(
        chip_mac="AA:BB:CC:DD:EE:FF",
        node_type="sensor_node",
    )
    assert d.chip_mac == "AA:BB:CC:DD:EE:FF"
    assert d.room_id is None
    assert d.capabilities is None


def test_device_schema_missing_required():
    with pytest.raises(ValidationError):
        Device(node_type="sensor_node")  # Missing chip_mac
