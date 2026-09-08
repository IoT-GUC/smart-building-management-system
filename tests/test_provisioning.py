from __future__ import annotations

import pytest
import sqlite3
from unittest.mock import patch
from pydantic import ValidationError
from fastapi.testclient import TestClient

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
        capabilities=["environment"],
        payload_encoder_key="temp_v1",
        uplink_interval_seconds=60,
        firmware_version="1.0.0",
    )
    assert d.chip_mac == "AA:BB:CC:DD:EE:FF"
    assert d.node_type == "sensor_node"
    assert d.room_id == 1
    assert d.capabilities == ["environment"]


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


def test_post_provision_endpoint(client: TestClient, db_conn: sqlite3.Connection):
    db_conn.execute("INSERT OR REPLACE INTO clients (id, name) VALUES (1, 'Test Client')")
    db_conn.execute("INSERT OR REPLACE INTO sites (id, client_id, name) VALUES (1, 1, 'Test Site')")
    db_conn.execute("INSERT OR REPLACE INTO buildings (id, site_id, name) VALUES (1, 1, 'Building A')")
    db_conn.execute("INSERT OR REPLACE INTO floors (id, building_id, name, floor_number) VALUES (1, 1, 'Floor 1', 1)")
    db_conn.execute("INSERT OR REPLACE INTO rooms (id, floor_id, room_name, polygon_points, x, y) VALUES (999, 1, 'Room 999', '[]', 0, 0)")
    db_conn.execute("""
        INSERT OR REPLACE INTO sensor_profiles (
            id, profile_code, profile_name, node_type, profile_version, payload_version,
            payload_encoder_key, uplink_interval_seconds, ttn_formatter_code, enabled, status
        ) VALUES (
            99, 'TEST_V1', 'Temperature Sensor', 'environment', 1, 1,
            'temp_v1', 60, 'js_code', 1, 'active'
        )
    """)
    db_conn.commit()

    payload = {
        "chip_mac": "AA:BB:CC:DD:EE:FF",
        "node_type": "environment",
        "room_id": 999,
        "profile_id": 99,
        "profile_code": "TEST_V1",
        "profile_version": 1,
        "payload_version": 1,
        "payload_encoder_key": "temp_v1",
        "uplink_interval_seconds": 60,
        "building": "Building A",
        "floor": "Floor 1",
        "room": "Room 999"
    }

    with patch("app.main.register_device_in_ttn") as mock_ttn, \
         patch("app.main.sync_tb_attributes_from_profile") as mock_tb, \
         patch("app.main.validate_config"):
        
        mock_tb.return_value = {"status": "ok", "profile_code": "TEST_V1", "tb_device_profile_name": "default"}

        res = client.post("/provision", json=payload)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] in ("created", "existing_updated")
        assert data["room_id"] == 999
