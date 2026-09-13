from __future__ import annotations

import hashlib
import re


def normalize_hex(value: str, expected_length: int, field_name: str) -> str:
    normalized = re.sub(r"[^0-9A-Fa-f]", "", str(value or "")).upper()
    if len(normalized) != expected_length:
        raise ValueError(
            f"{field_name} must contain exactly {expected_length} hexadecimal characters"
        )
    return normalized


def dev_eui_namespace_mask(namespace: str) -> str:
    """Return the stable eight-byte mask used to namespace hardware DevEUIs."""
    clean_namespace = str(namespace or "").strip().lower()
    if not clean_namespace:
        raise ValueError("DevEUI namespace must not be empty")
    return hashlib.sha256(clean_namespace.encode("utf-8")).digest()[:8].hex().upper()


def derive_dev_eui_from_mac(chip_mac: str, *, namespace: str | None = None) -> str:
    """Match the app-scoped EUI-64 derivation used by the ESP32 firmware."""
    mac = normalize_hex(chip_mac, 12, "chip_mac")
    base = bytes.fromhex(f"{mac[:6]}FFFE{mac[6:]}")
    if namespace:
        mask = bytes.fromhex(dev_eui_namespace_mask(namespace))
        base = bytes(left ^ right for left, right in zip(base, mask, strict=True))
    return base.hex().upper()


def device_id_from_dev_eui(dev_eui: str) -> str:
    return f"eui-{normalize_hex(dev_eui, 16, 'dev_eui').lower()}"
