import logging
logger = logging.getLogger(__name__)

import sqlite3
import json
from fastapi import HTTPException
from app.config import settings
from app.routers.api import Device


def validate_provision_location_and_type(conn: sqlite3.Connection, device: Device):
    from app.main import db, normalize_mac, normalize_eui, JOIN_EUI, validate_config, get_existing_device, make_device_id, generate_unique_dev_eui, generate_app_key, get_auto_room_position, register_device_in_ttn, save_device, save_device_profile_assignment, save_device_capabilities, record_device_configuration_history, sync_tb_attributes_from_profile, update_existing_device_metadata, set_device_formatter_from_profile, get_sensor_profile_row, get_firmware_module_detail, get_sensor_catalog_detail, get_room_from_database, firmware_version_tuple, firmware_version_is_compatible

    node_type = device.node_type.lower().strip()

    if node_type not in ALLOWED_NODE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid node_type. Allowed values: {sorted(ALLOWED_NODE_TYPES)}",
        )

    room_row = get_room_from_database(
        conn=conn,
        building=device.building,
        floor=device.floor,
        room_name=device.room,
    )

    if not room_row:
        raise HTTPException(
            status_code=400,
            detail=f"Room not found in database: building={device.building}, floor={device.floor}, room={device.room}",
        )

    return node_type



def get_room_by_id_for_provision(conn: sqlite3.Connection, room_id: int):
    from app.main import db, normalize_mac, normalize_eui, JOIN_EUI, validate_config, get_existing_device, make_device_id, generate_unique_dev_eui, generate_app_key, get_auto_room_position, register_device_in_ttn, save_device, save_device_profile_assignment, save_device_capabilities, record_device_configuration_history, sync_tb_attributes_from_profile, update_existing_device_metadata, set_device_formatter_from_profile, get_sensor_profile_row, get_firmware_module_detail, get_sensor_catalog_detail, get_room_from_database, firmware_version_tuple, firmware_version_is_compatible

    row = conn.execute("""
        SELECT
            r.id AS room_id,
            r.room_name,
            r.building,
            r.floor,
            r.x,
            r.y,
            r.floor_id,
            f.building_id,
            b.site_id,
            s.client_id
        FROM rooms r
        LEFT JOIN floors f ON r.floor_id = f.id
        LEFT JOIN buildings b ON f.building_id = b.id
        LEFT JOIN sites s ON b.site_id = s.id
        WHERE r.id = ?
        LIMIT 1
    """, (room_id,)).fetchone()

    return row





def normalize_provision_capabilities(node_type: str, capabilities: list | None = None):
    from app.main import db, normalize_mac, normalize_eui, JOIN_EUI, validate_config, get_existing_device, make_device_id, generate_unique_dev_eui, generate_app_key, get_auto_room_position, register_device_in_ttn, save_device, save_device_profile_assignment, save_device_capabilities, record_device_configuration_history, sync_tb_attributes_from_profile, update_existing_device_metadata, set_device_formatter_from_profile, get_sensor_profile_row, get_firmware_module_detail, get_sensor_catalog_detail, get_room_from_database, firmware_version_tuple, firmware_version_is_compatible

    allowed = {
        "environment",
        "energy",
        "safety",
        "occupancy"
    }

    node_type = node_type.strip().lower()

    clean = []

    if capabilities:
        for cap in capabilities:
            cap = str(cap).strip().lower()

            if cap not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid capability: {cap}"
                )

            if cap not in clean:
                clean.append(cap)

    if node_type == "multi":
        if clean:
            return clean

        return [
            "environment",
            "energy",
            "safety",
            "occupancy"
        ]

    if node_type in allowed:
        return [node_type]

    return []



def provision(device: Device):
    from app.main import db, normalize_mac, normalize_eui, JOIN_EUI, validate_config, get_existing_device, make_device_id, generate_unique_dev_eui, generate_app_key, get_auto_room_position, register_device_in_ttn, save_device, save_device_profile_assignment, save_device_capabilities, record_device_configuration_history, sync_tb_attributes_from_profile, update_existing_device_metadata, set_device_formatter_from_profile, get_sensor_profile_row, get_firmware_module_detail, get_sensor_catalog_detail, get_room_from_database, firmware_version_tuple, firmware_version_is_compatible

    """
    Provision or update a LILYGO using a backend-validated sensor
    profile and a stable room_id.
    """

    # ---------------------------------------------------------
    # 1. Validate environment and ESP32 identity
    # ---------------------------------------------------------

    try:
        validate_config()

        chip_mac = normalize_mac(
            device.chip_mac
        )

        join_eui = normalize_eui(
            JOIN_EUI,
            16,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

    conn = db()

    try:
        # -----------------------------------------------------
        # 2. Resolve and validate the selected sensor profile
        # -----------------------------------------------------

        profile = resolve_sensor_profile_for_provision(
            conn,
            device,
        )

        # From this point, the database profile is the source
        # of truth rather than the browser-submitted values.
        node_type = profile["node_type"]
        capabilities = profile["capabilities"]

        device.node_type = node_type
        device.capabilities = capabilities

        # -----------------------------------------------------
        # 3. Require and resolve the stable room ID
        # -----------------------------------------------------

        if device.room_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "room_id is required for profile-driven "
                    "provisioning"
                ),
            )

        resolved_room = get_room_by_id_for_provision(
            conn,
            device.room_id,
        )

        if not resolved_room:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Room not found by room_id: "
                    f"{device.room_id}"
                ),
            )

        # Never trust the submitted location names when room_id
        # already identifies the canonical database room.
        device.building = resolved_room["building"]
        device.floor = resolved_room["floor"]
        device.room = resolved_room["room_name"]
        device.room_id = resolved_room["room_id"]

        # This also confirms that the room exists and that the
        # canonical profile node type remains valid.
        validate_provision_location_and_type(
            conn,
            device,
        )

        # -----------------------------------------------------
        # 4. Prepare display metadata
        # -----------------------------------------------------

        clean_label = str(
            device.label or ""
        ).strip()

        if clean_label:
            label = clean_label
        else:
            label = (
                f"{profile['profile_name']} - "
                f"{device.room}"
            )

        final_icon_type = (
            profile["icon_type"]
            or infer_icon_type(node_type)
        )

        # -----------------------------------------------------
        # 5. Update an already provisioned ESP32
        # -----------------------------------------------------

        existing = get_existing_device(
            conn,
            chip_mac,
        )

        if existing:
            if (
                device.x is not None
                and device.y is not None
            ):
                final_x = device.x
                final_y = device.y
            else:
                final_x, final_y = get_auto_room_position(
                    conn=conn,
                    building=device.building,
                    floor=device.floor,
                    room=device.room,
                    exclude_chip_mac=chip_mac,
                )

            update_existing_device_metadata(
                conn=conn,
                chip_mac=chip_mac,
                node_type=node_type,
                building=device.building,
                floor=device.floor,
                room=device.room,
                label=label,
                x=final_x,
                y=final_y,
                icon_type=final_icon_type,
            )

            conn.execute(
                """
                UPDATE devices
                SET
                    client_id = ?,
                    site_id = ?,
                    building_id = ?,
                    floor_id = ?,
                    room_id = ?
                WHERE chip_mac = ?
                """,
                (
                    resolved_room["client_id"],
                    resolved_room["site_id"],
                    resolved_room["building_id"],
                    resolved_room["floor_id"],
                    resolved_room["room_id"],
                    chip_mac,
                ),
            )

            save_device_profile_assignment(
                conn=conn,
                chip_mac=chip_mac,
                profile=profile,
            )

            updated = get_existing_device(
                conn,
                chip_mac,
            )

            save_device_capabilities(
                conn,
                updated["device_id"],
                capabilities,
            )

            record_device_configuration_history(
                conn=conn,
                device_row=updated,
                profile=profile,
                provision_status="existing_updated",
                source="lilygo_provisioning",
                requested_by=chip_mac,
            )

            conn.commit()
            # The next implementation step will replace this
            # legacy node-type formatter selection with the
            # formatter stored directly in the profile.
            try:
                set_device_formatter_from_profile(
                    device_id=updated["device_id"],
                    profile=profile,
                )
            except Exception as exc:
                logger.info(
                    "Profile formatter update failed:",
                    exc,
                )

            try:
                updated = get_existing_device(
                    conn,
                    chip_mac,
                )

                tb_sync_result = (
                    sync_tb_attributes_from_profile(
                        device_row=updated,
                        profile=profile,
                    )
                )

                logger.info(
                    "Profile-driven ThingsBoard sync:",
                    tb_sync_result["status"],
                    tb_sync_result["profile_code"],
                    tb_sync_result[
                        "tb_device_profile_name"
                    ],
                )

            except Exception as exc:
                logger.info(
                    "Profile-driven ThingsBoard "
                    "attribute sync failed:",
                    exc,
                )

            final_row = get_existing_device(
                conn,
                chip_mac,
            )

            return build_profile_provision_response(
                status="existing_updated",
                device_row=final_row,
                profile=profile,
                capabilities=capabilities,
            )

        # -----------------------------------------------------
        # 6. Create a new device
        # -----------------------------------------------------

        device_id = make_device_id(
            chip_mac
        )

        dev_eui = generate_unique_dev_eui(
            conn
        )

        app_key = generate_app_key()

        if (
            device.x is not None
            and device.y is not None
        ):
            final_x = device.x
            final_y = device.y
        else:
            final_x, final_y = get_auto_room_position(
                conn=conn,
                building=device.building,
                floor=device.floor,
                room=device.room,
            )

        # Current legacy registration remains operational for
        # the seeded compatibility profiles. Profile-based TTN
        # formatter installation comes in the next step.
        register_device_in_ttn(
            device_id=device_id,
            dev_eui=dev_eui,
            join_eui=join_eui,
            app_key=app_key,
            profile=profile,
        )

        save_device(
            conn=conn,
            chip_mac=chip_mac,
            device_id=device_id,
            dev_eui=dev_eui,
            join_eui=join_eui,
            app_key=app_key,
            node_type=node_type,
            building=device.building,
            floor=device.floor,
            room=device.room,
            label=label,
            x=final_x,
            y=final_y,
            icon_type=final_icon_type,
        )

        conn.execute(
            """
            UPDATE devices
            SET
                client_id = ?,
                site_id = ?,
                building_id = ?,
                floor_id = ?,
                room_id = ?
            WHERE chip_mac = ?
            """,
            (
                resolved_room["client_id"],
                resolved_room["site_id"],
                resolved_room["building_id"],
                resolved_room["floor_id"],
                resolved_room["room_id"],
                chip_mac,
            ),
        )

        save_device_profile_assignment(
            conn=conn,
            chip_mac=chip_mac,
            profile=profile,
        )

        save_device_capabilities(
            conn,
            device_id,
            capabilities,
        )

        saved = get_existing_device(
            conn,
            chip_mac,
        )

        record_device_configuration_history(
            conn=conn,
            device_row=saved,
            profile=profile,
            provision_status="created",
            source="lilygo_provisioning",
            requested_by=chip_mac,
        )

        conn.commit()
        try:
            tb_sync_result = (
                sync_tb_attributes_from_profile(
                    device_row=saved,
                    profile=profile,
                )
            )

            logger.info(
                "Profile-driven ThingsBoard sync:",
                tb_sync_result["status"],
                tb_sync_result["profile_code"],
                tb_sync_result[
                    "tb_device_profile_name"
                ],
            )

        except Exception as exc:
            logger.info(
                "Profile-driven ThingsBoard "
                "attribute sync failed:",
                exc,
            )

        final_row = get_existing_device(
            conn,
            chip_mac,
        )

        return build_profile_provision_response(
            status="created",
            device_row=final_row,
            profile=profile,
            capabilities=capabilities,
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()

        logger.info(
            "Profile-driven provisioning failed:",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Profile-driven provisioning failed: "
                f"{exc}"
            ),
        )

    finally:
        conn.close()

