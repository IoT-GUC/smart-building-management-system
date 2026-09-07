from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class Device(BaseModel):
    """
    Provisioning request model.

    chip_mac and node_type are always required.
    All other fields are optional to support both
    profile-driven and legacy provisioning flows.
    """

    # --- ESP32 identity ---
    chip_mac: str
    node_type: str

    # --- Canonical location (preferred: room_id) ---
    room_id: Optional[int] = None

    # --- Temporary compatibility fields (derived from room_id when present) ---
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None

    # --- Stable sensor-profile identity ---
    profile_id: Optional[int] = None
    profile_code: Optional[str] = None
    profile_version: Optional[int] = None

    # --- Payload contract selected by the profile ---
    payload_version: Optional[int] = None
    payload_encoder_key: Optional[str] = None
    uplink_interval_seconds: Optional[int] = None
    firmware_version: Optional[str] = None

    # --- Device capabilities (derived from profile when using profile flow) ---
    capabilities: Optional[List[str]] = None

    # --- Display / floor-map metadata ---
    label: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    icon_type: Optional[str] = None


class ProfileAlarmTemplateValues(dict):
    """
    Preserve an unknown placeholder instead of causing the alarm
    engine to fail because of one custom message template.
    """

    def __missing__(self, key: str) -> str:  # type: ignore[override]
        return "{" + str(key) + "}"
