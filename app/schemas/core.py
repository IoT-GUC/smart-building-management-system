from pydantic import BaseModel

class Device(BaseModel):
    # ESP32 identity
    chip_mac: str

    # Legacy compatibility value.
    # The backend will verify it against the selected profile.
    node_type: str

    # Stable sensor-profile identity
    profile_id: int | None = None
    profile_code: str | None = None
    profile_version: int | None = None

    # Payload contract selected by the profile
    payload_version: int | None = None

class ProfileAlarmTemplateValues(dict):
    """
    Preserve an unknown placeholder instead of causing the alarm
    engine to fail because of one custom message template.
    """

    def __missing__(self, key):
        return "{" + str(key) + "}"
