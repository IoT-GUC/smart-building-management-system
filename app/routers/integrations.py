import logging
logger = logging.getLogger(__name__)

import os
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, FileResponse, RedirectResponse
import json
import sqlite3
import csv
import io
import re
from app.main import *
router = APIRouter()

@router.get("/provision-options")
def provision_options():
    """
    Return the location hierarchy and all active sensor profiles
    available for LILYGO provisioning.

    Compatibility:
    - profiles: new profile-driven provisioning architecture.
    - node_types: retained for the current legacy firmware.
    """

    conn = db()

    try:
        # =====================================================
        # 1. LOAD PROVISIONABLE ROOMS
        # =====================================================

        room_rows = conn.execute(
            """
            SELECT
                rooms.id,
                rooms.building,
                rooms.floor,
                rooms.room_name,
                rooms.x,
                rooms.y,
                rooms.floor_id
            FROM rooms
            WHERE rooms.floor_id IS NOT NULL
            ORDER BY
                rooms.building,
                rooms.floor,
                rooms.room_name
            """
        ).fetchall()

        buildings = {}

        for row in room_rows:
            building_name = row["building"]
            floor_name = row["floor"]
            room_name = row["room_name"]

            if building_name not in buildings:
                buildings[building_name] = {}

            if floor_name not in buildings[building_name]:
                buildings[building_name][floor_name] = {}

            buildings[building_name][floor_name][room_name] = {
                "room_id": row["id"],
                "floor_id": row["floor_id"],
                "x": row["x"],
                "y": row["y"],
            }

        # =====================================================
        # 2. LOAD ACTIVE SENSOR PROFILES
        # =====================================================

        profile_rows = conn.execute(
            """
            SELECT
                id,
                profile_code,
                profile_name,
                profile_version,
                node_type,
                description,

                capabilities_json,
                configuration_schema_json,

                payload_encoder_key,
                payload_version,
                f_port,
                uplink_interval_seconds,

                icon_type,
                icon_color,

                status,
                enabled,
                schema_checksum

            FROM sensor_profiles

            WHERE enabled = 1
              AND status = 'active'

            ORDER BY
                profile_name,
                profile_version DESC
            """
        ).fetchall()

        profiles = []

        for profile_row in profile_rows:
            profile_id = profile_row["id"]

            # -------------------------------------------------
            # Physical sensors and firmware modules
            # -------------------------------------------------

            sensor_rows = conn.execute(
                """
                SELECT
                    relation.role,
                    relation.required,
                    relation.configuration_json,
                    relation.display_order,

                    catalog.sensor_code,
                    catalog.manufacturer,
                    catalog.model,
                    catalog.use_case,
                    catalog.protocol,
                    catalog.default_bus,
                    catalog.default_address,

                    module.module_key,
                    module.display_name AS module_name,
                    module.driver_class,
                    module.library_name,
                    module.library_version,
                    module.supported_board,
                    module.min_firmware_version

                FROM sensor_profile_sensors relation

                INNER JOIN sensor_catalog catalog
                    ON catalog.id = relation.sensor_id

                LEFT JOIN firmware_modules module
                    ON module.id = relation.firmware_module_id

                WHERE relation.profile_id = ?

                ORDER BY
                    relation.display_order,
                    relation.id
                """,
                (profile_id,),
            ).fetchall()

            sensor_components = []

            for sensor_row in sensor_rows:
                sensor_components.append(
                    {
                        "sensor_code": sensor_row[
                            "sensor_code"
                        ],
                        "manufacturer": sensor_row[
                            "manufacturer"
                        ],
                        "model": sensor_row["model"],
                        "use_case": sensor_row["use_case"],
                        "protocol": sensor_row["protocol"],
                        "default_bus": sensor_row[
                            "default_bus"
                        ],
                        "default_address": sensor_row[
                            "default_address"
                        ],
                        "role": sensor_row["role"],
                        "required": bool(
                            sensor_row["required"]
                        ),
                        "configuration": profile_json_load(
                            sensor_row[
                                "configuration_json"
                            ],
                            {},
                        ),
                        "firmware_module": {
                            "module_key": sensor_row[
                                "module_key"
                            ],
                            "module_name": sensor_row[
                                "module_name"
                            ],
                            "driver_class": sensor_row[
                                "driver_class"
                            ],
                            "library_name": sensor_row[
                                "library_name"
                            ],
                            "library_version": sensor_row[
                                "library_version"
                            ],
                            "supported_board": sensor_row[
                                "supported_board"
                            ],
                            "min_firmware_version": (
                                sensor_row[
                                    "min_firmware_version"
                                ]
                            ),
                        },
                    }
                )

            # -------------------------------------------------
            # Telemetry/payload field definitions
            # -------------------------------------------------

            field_rows = conn.execute(
                """
                SELECT
                    field_key,
                    label,
                    unit,
                    data_type,

                    payload_order,
                    byte_offset,
                    byte_length,
                    scale,
                    signed,
                    endianness,

                    required,
                    nullable,

                    min_value,
                    max_value

                FROM sensor_profile_fields

                WHERE profile_id = ?

                ORDER BY
                    payload_order,
                    display_order,
                    id
                """,
                (profile_id,),
            ).fetchall()

            telemetry_fields = []

            for field_row in field_rows:
                telemetry_fields.append(
                    {
                        "field_key": field_row["field_key"],
                        "label": field_row["label"],
                        "unit": field_row["unit"],
                        "data_type": field_row["data_type"],
                        "payload_order": field_row[
                            "payload_order"
                        ],
                        "byte_offset": field_row[
                            "byte_offset"
                        ],
                        "byte_length": field_row[
                            "byte_length"
                        ],
                        "scale": field_row["scale"],
                        "signed": bool(
                            field_row["signed"]
                        ),
                        "endianness": field_row[
                            "endianness"
                        ],
                        "required": bool(
                            field_row["required"]
                        ),
                        "nullable": bool(
                            field_row["nullable"]
                        ),
                        "min_value": field_row[
                            "min_value"
                        ],
                        "max_value": field_row[
                            "max_value"
                        ],
                    }
                )

            # -------------------------------------------------
            # Required firmware features
            # -------------------------------------------------

            compatibility_rows = conn.execute(
                """
                SELECT
                    module.module_key,
                    compatibility.min_firmware_version,
                    compatibility.max_firmware_version,
                    compatibility.hardware_revision,
                    compatibility.required_features_json

                FROM profile_firmware_compatibility compatibility

                INNER JOIN firmware_modules module
                    ON module.id = (
                        compatibility.firmware_module_id
                    )

                WHERE compatibility.profile_id = ?
                  AND compatibility.enabled = 1

                ORDER BY module.module_key
                """,
                (profile_id,),
            ).fetchall()

            firmware_compatibility = []

            for compatibility_row in compatibility_rows:
                firmware_compatibility.append(
                    {
                        "module_key": compatibility_row[
                            "module_key"
                        ],
                        "min_firmware_version": (
                            compatibility_row[
                                "min_firmware_version"
                            ]
                        ),
                        "max_firmware_version": (
                            compatibility_row[
                                "max_firmware_version"
                            ]
                        ),
                        "hardware_revision": (
                            compatibility_row[
                                "hardware_revision"
                            ]
                        ),
                        "required_features": (
                            profile_json_load(
                                compatibility_row[
                                    "required_features_json"
                                ],
                                [],
                            )
                        ),
                    }
                )

            profiles.append(
                {
                    "profile_id": profile_id,
                    "profile_code": profile_row[
                        "profile_code"
                    ],
                    "profile_name": profile_row[
                        "profile_name"
                    ],
                    "profile_version": profile_row[
                        "profile_version"
                    ],
                    "node_type": profile_row["node_type"],
                    "description": profile_row[
                        "description"
                    ],
                    "capabilities": profile_json_load(
                        profile_row[
                            "capabilities_json"
                        ],
                        [],
                    ),
                    "configuration_schema": (
                        profile_json_load(
                            profile_row[
                                "configuration_schema_json"
                            ],
                            {},
                        )
                    ),
                    "payload_encoder_key": profile_row[
                        "payload_encoder_key"
                    ],
                    "payload_version": profile_row[
                        "payload_version"
                    ],
                    "f_port": profile_row["f_port"],
                    "uplink_interval_seconds": (
                        profile_row[
                            "uplink_interval_seconds"
                        ]
                    ),
                    "icon_type": profile_row["icon_type"],
                    "icon_color": profile_row["icon_color"],
                    "schema_checksum": profile_row[
                        "schema_checksum"
                    ],
                    "sensor_components": sensor_components,
                    "telemetry_fields": telemetry_fields,
                    "firmware_compatibility": (
                        firmware_compatibility
                    ),
                }
            )

        # =====================================================
        # 3. RETAIN LEGACY NODE TYPES
        # =====================================================

        profile_node_types = {
            profile["node_type"]
            for profile in profiles
            if profile.get("node_type")
        }

        available_node_types = sorted(
            set(ALLOWED_NODE_TYPES)
            | profile_node_types
        )

        return {
            "status": "ok",
            "profile_architecture_version": 1,
            "profile_count": len(profiles),

            # New provisioning architecture
            "profiles": profiles,

            # Legacy firmware compatibility
            "node_types": available_node_types,

            # Location hierarchy
            "buildings": buildings,
        }

    finally:
        conn.close()
@router.post("/provision")
def provision(device: Device):
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