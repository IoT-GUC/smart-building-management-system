from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse, FileResponse
from maintestfinal2 import *

router = APIRouter()

@router.put("/users/{user_id}/credentials")
def update_user_credentials(user_id: int, data: dict, request: Request):
    current_user = get_current_user_from_request(request)

    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")

    if (current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    enabled = data.get("enabled")

    conn = db()

    user_row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
    """, (user_id,)).fetchone()

    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    old_user = dict(user_row)

    if (old_user.get("role") or "").lower() != "client":
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="This endpoint is only for client user credentials"
        )

    updates = []
    params = []
    changed_fields = {}

    if name is not None:
        clean_name = str(name).strip()

        if not clean_name:
            conn.close()
            raise HTTPException(status_code=400, detail="Name cannot be empty")

        updates.append("name = ?")
        params.append(clean_name)
        changed_fields["name"] = {
            "old": old_user.get("name"),
            "new": clean_name
        }

    if email is not None:
        clean_email = str(email).strip().lower()

        if not clean_email:
            conn.close()
            raise HTTPException(status_code=400, detail="Email cannot be empty")

        existing_email = conn.execute("""
            SELECT id
            FROM users
            WHERE email = ?
              AND id != ?
            LIMIT 1
        """, (clean_email, user_id)).fetchone()

        if existing_email:
            conn.close()
            raise HTTPException(
                status_code=409,
                detail="Another user already uses this email"
            )

        updates.append("email = ?")
        params.append(clean_email)
        changed_fields["email"] = {
            "old": old_user.get("email"),
            "new": clean_email
        }

    if enabled is not None:
        enabled_value = 1 if enabled in [1, "1", True, "true", "True", "yes", "on"] else 0

        updates.append("enabled = ?")
        params.append(enabled_value)
        changed_fields["enabled"] = {
            "old": old_user.get("enabled"),
            "new": enabled_value
        }

    if password is not None and str(password).strip() != "":
        clean_password = str(password)

        if len(clean_password) < 8:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters"
            )

        password_data = create_password_hash(clean_password)

        updates.append("password_salt = ?")
        params.append(password_data["password_salt"])

        updates.append("password_hash = ?")
        params.append(password_data["password_hash"])

        updates.append("password_iterations = ?")
        params.append(password_data["password_iterations"])

        updates.append("password_updated_at = CURRENT_TIMESTAMP")

        changed_fields["password"] = {
            "old": "***hidden***",
            "new": "***updated***"
        }

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No credential fields provided")

    params.append(user_id)

    conn.execute(f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE id = ?
    """, params)

    conn.commit()

    updated_user_row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
    """, (user_id,)).fetchone()

    updated_user = safe_user_dict(updated_user_row)

    log_audit_event(
        conn=conn,
        action="update_client_credentials",
        actor=current_user.get("email", "admin"),
        target_type="user",
        target_id=user_id,
        user_id=user_id,
        details={
            "old": {
                "id": old_user.get("id"),
                "name": old_user.get("name"),
                "email": old_user.get("email"),
                "role": old_user.get("role"),
                "enabled": old_user.get("enabled"),
                "password_updated_at": old_user.get("password_updated_at")
            },
            "new": updated_user,
            "changed_fields": changed_fields
        }
    )

    conn.close()

    return {
        "status": "credentials_updated",
        "user": updated_user,
        "changed_fields": changed_fields
    }

@router.get("/alarms/export.csv")
def export_alarm_history_csv(
    limit: int = 1000,
    device_id: str = None,
    node_type: str = None,
    alarm_type: str = None,
    building: str = None,
    floor: str = None,
    room: str = None,
    acknowledged: int = None,
    resolved: int = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None
):
    conn = db()

    where_clauses = []
    params = []

    def add_filter(column_name, value):
        if value is not None and value != "":
            where_clauses.append(f"{column_name} = ?")
            params.append(value)

    add_filter("device_id", device_id)
    add_filter("node_type", node_type)
    add_filter("alarm_type", alarm_type)
    add_filter("building", building)
    add_filter("floor", floor)
    add_filter("room", room)
    add_filter("acknowledged", acknowledged)
    add_filter("resolved", resolved)

    if search:
        where_clauses.append("""
            (
                device_id LIKE ?
                OR node_type LIKE ?
                OR building LIKE ?
                OR floor LIKE ?
                OR room LIKE ?
                OR alarm_type LIKE ?
                OR alarm_message LIKE ?
                OR telemetry LIKE ?
            )
        """)

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if from_date:
        where_clauses.append("triggered_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("triggered_at <= ?")

        if len(to_date) == 10:
            params.append(to_date + " 23:59:59")
        else:
            params.append(to_date)

    where_sql = ""

    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    if limit < 1:
        limit = 1000

    if limit > 5000:
        limit = 5000

    rows = conn.execute(f"""
        SELECT *
        FROM alarm_history
        {where_sql}
        ORDER BY datetime(triggered_at) DESC, id DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    output = io.StringIO()

    fieldnames = [
        "id",
        "device_id",
        "node_type",
        "building",
        "floor",
        "room",
        "alarm_type",
        "alarm_message",
        "triggered_at",
        "acknowledged",
        "acknowledged_by",
        "acknowledged_at",
        "resolved",
        "resolved_by",
        "resolved_at",
        "telemetry"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        item = dict(row)

        try:
            telemetry_obj = json.loads(item["telemetry"]) if item.get("telemetry") else {}
            telemetry_text = json.dumps(telemetry_obj, ensure_ascii=False)
        except Exception:
            telemetry_text = item.get("telemetry") or ""

        writer.writerow({
            "id": item.get("id"),
            "device_id": item.get("device_id"),
            "node_type": item.get("node_type"),
            "building": item.get("building"),
            "floor": item.get("floor"),
            "room": item.get("room"),
            "alarm_type": item.get("alarm_type"),
            "alarm_message": item.get("alarm_message"),
            "triggered_at": item.get("triggered_at"),
            "acknowledged": item.get("acknowledged"),
            "acknowledged_by": item.get("acknowledged_by"),
            "acknowledged_at": item.get("acknowledged_at"),
            "resolved": item.get("resolved"),
            "resolved_by": item.get("resolved_by"),
            "resolved_at": item.get("resolved_at"),
            "telemetry": telemetry_text
        })

    conn.close()

    output.seek(0)

    export_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"alarm_history_export_{export_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )    

@router.get("/admin/export/full-structure.csv")
def admin_full_structure_export_csv():
    conn = db()

    def rows_to_dicts(query):
        return [dict(row) for row in conn.execute(query).fetchall()]

    def clean_details(data):
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return str(data)

    def get_name(row, keys=("name", "label", "title")):
        if not row:
            return ""

        for key in keys:
            value = row.get(key)
            if value:
                return value

        return ""

    clients = rows_to_dicts("SELECT * FROM clients ORDER BY id")
    sites = rows_to_dicts("SELECT * FROM sites ORDER BY id")
    buildings = rows_to_dicts("SELECT * FROM buildings ORDER BY id")
    floors = rows_to_dicts("SELECT * FROM floors ORDER BY id")
    rooms = rows_to_dicts("SELECT * FROM rooms ORDER BY id")
    devices = rows_to_dicts("SELECT * FROM devices ORDER BY device_id")
    gateways = rows_to_dicts("SELECT * FROM gateways ORDER BY id")

    clients_by_id = {row.get("id"): row for row in clients}
    sites_by_id = {row.get("id"): row for row in sites}
    buildings_by_id = {row.get("id"): row for row in buildings}
    floors_by_id = {row.get("id"): row for row in floors}
    rooms_by_id = {row.get("id"): row for row in rooms}

    output = io.StringIO()

    fieldnames = [
        "record_type",
        "client_id",
        "client_name",
        "site_id",
        "site_name",
        "building_id",
        "building_name",
        "floor_id",
        "floor_name",
        "floor_number",
        "room_id",
        "room_name",
        "asset_type",
        "asset_id",
        "asset_name",
        "device_id",
        "gateway_id",
        "node_type",
        "status",
        "x",
        "y",
        "label",
        "location_note",
        "last_seen",
        "created_at",
        "details"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    def write_row(
        record_type,
        client=None,
        site=None,
        building=None,
        floor=None,
        room=None,
        asset_type="",
        asset_id="",
        asset_name="",
        device_id="",
        gateway_id="",
        node_type="",
        status="",
        x="",
        y="",
        label="",
        location_note="",
        last_seen="",
        created_at="",
        details=None
    ):
        writer.writerow({
            "record_type": record_type,

            "client_id": client.get("id") if client else "",
            "client_name": get_name(client),

            "site_id": site.get("id") if site else "",
            "site_name": get_name(site),

            "building_id": building.get("id") if building else "",
            "building_name": get_name(building),

            "floor_id": floor.get("id") if floor else "",
            "floor_name": get_name(floor),
            "floor_number": floor.get("floor_number") if floor else "",

            "room_id": room.get("id") if room else "",
            "room_name": get_name(room),

            "asset_type": asset_type,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "device_id": device_id,
            "gateway_id": gateway_id,
            "node_type": node_type,
            "status": status,
            "x": x,
            "y": y,
            "label": label,
            "location_note": location_note,
            "last_seen": last_seen,
            "created_at": created_at,
            "details": clean_details(details or {})
        })

    # 1. Clients
    for client in clients:
        write_row(
            record_type="CLIENT",
            client=client,
            asset_type="client",
            asset_id=client.get("id"),
            asset_name=get_name(client),
            created_at=client.get("created_at", ""),
            details=client
        )

    # 2. Sites
    for site in sites:
        client = clients_by_id.get(site.get("client_id"))

        write_row(
            record_type="SITE",
            client=client,
            site=site,
            asset_type="site",
            asset_id=site.get("id"),
            asset_name=get_name(site),
            created_at=site.get("created_at", ""),
            details=site
        )

    # 3. Buildings
    for building in buildings:
        site = sites_by_id.get(building.get("site_id"))
        client = clients_by_id.get(site.get("client_id")) if site else None

        write_row(
            record_type="BUILDING",
            client=client,
            site=site,
            building=building,
            asset_type="building",
            asset_id=building.get("id"),
            asset_name=get_name(building),
            created_at=building.get("created_at", ""),
            details=building
        )

    # 4. Floors
    for floor in floors:
        building = buildings_by_id.get(floor.get("building_id"))
        site = sites_by_id.get(building.get("site_id")) if building else None
        client = clients_by_id.get(site.get("client_id")) if site else None

        write_row(
            record_type="FLOOR",
            client=client,
            site=site,
            building=building,
            floor=floor,
            asset_type="floor",
            asset_id=floor.get("id"),
            asset_name=get_name(floor),
            created_at=floor.get("created_at", ""),
            details=floor
        )

    # 5. Rooms
    for room in rooms:
        floor = floors_by_id.get(room.get("floor_id"))
        building = buildings_by_id.get(floor.get("building_id")) if floor else None
        site = sites_by_id.get(building.get("site_id")) if building else None
        client = clients_by_id.get(site.get("client_id")) if site else None

        write_row(
            record_type="ROOM",
            client=client,
            site=site,
            building=building,
            floor=floor,
            room=room,
            asset_type="room",
            asset_id=room.get("id"),
            asset_name=get_name(room),
            x=room.get("x", ""),
            y=room.get("y", ""),
            created_at=room.get("created_at", ""),
            details=room
        )

    # 6. Devices / Nodes
    for device in devices:
        room = rooms_by_id.get(device.get("room_id"))
        floor = floors_by_id.get(room.get("floor_id")) if room else floors_by_id.get(device.get("floor_id"))
        building = buildings_by_id.get(floor.get("building_id")) if floor else buildings_by_id.get(device.get("building_id"))
        site = sites_by_id.get(building.get("site_id")) if building else sites_by_id.get(device.get("site_id"))
        client = clients_by_id.get(site.get("client_id")) if site else clients_by_id.get(device.get("client_id"))

        write_row(
            record_type="DEVICE",
            client=client,
            site=site,
            building=building,
            floor=floor,
            room=room,
            asset_type="device",
            asset_id=device.get("device_id"),
            asset_name=device.get("label") or device.get("device_id"),
            device_id=device.get("device_id"),
            node_type=device.get("node_type", ""),
            status=device.get("status", ""),
            x=device.get("x", ""),
            y=device.get("y", ""),
            label=device.get("label", ""),
            last_seen=device.get("last_seen", ""),
            created_at=device.get("created_at", ""),
            details=device
        )

    # 7. Gateways
    for gateway in gateways:
        floor = floors_by_id.get(gateway.get("floor_id"))
        building = buildings_by_id.get(gateway.get("building_id")) or (
            buildings_by_id.get(floor.get("building_id")) if floor else None
        )
        site = sites_by_id.get(gateway.get("site_id")) or (
            sites_by_id.get(building.get("site_id")) if building else None
        )
        client = clients_by_id.get(gateway.get("client_id")) or (
            clients_by_id.get(site.get("client_id")) if site else None
        )

        write_row(
            record_type="GATEWAY",
            client=client,
            site=site,
            building=building,
            floor=floor,
            room=None,
            asset_type="gateway",
            asset_id=gateway.get("gateway_id"),
            asset_name=gateway.get("label") or gateway.get("name") or gateway.get("gateway_id"),
            gateway_id=gateway.get("gateway_id"),
            status=gateway.get("status", ""),
            x=gateway.get("x", ""),
            y=gateway.get("y", ""),
            label=gateway.get("label", ""),
            location_note=gateway.get("location_note", ""),
            last_seen=gateway.get("last_seen", ""),
            created_at=gateway.get("created_at", ""),
            details=gateway
        )

    conn.close()

    output.seek(0)

    export_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"admin_full_structure_export_{export_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/")
def root():
    return {
        "status": "ok",
        "service": "LILYGO Provisioning Server",
        "app_id": APP_ID,
        "ttn_host": TTN_HOST,
        "thingsboard_url": THINGSBOARD_URL,
    }

@router.get("/gateways/{gateway_id}/sync")
def sync_gateway_status(gateway_id: str):
    gateway_record = ttn_get_gateway_status(gateway_id)
    connection_stats = ttn_get_gateway_connection_stats(gateway_id)

    if connection_stats:
        status = "online"
        last_seen = connection_stats.get("connected_at")
    else:
        status = "offline"
        last_seen = None

    conn = db()

    conn.execute("""
        UPDATE gateways
        SET status = ?,
            last_seen = ?
        WHERE gateway_id = ?
    """, (
        status,
        last_seen,
        gateway_id,
    ))

    conn.commit()

    row = conn.execute("""
        SELECT *
        FROM gateways
        WHERE gateway_id = ?
    """, (gateway_id,)).fetchone()

    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Gateway not found in backend database"
        )

    return {
        "status": "synced",
        "gateway": dict(row),
        "gateway_health": {
            "connection_status": status,
            "connected_at": last_seen,
            "stats": connection_stats
        },
        "ttn_gateway_record": gateway_record,
    }

@router.get("/gateways/health")
def gateways_health(site_id: int | None = None):
    conn = db()

    if site_id is not None:
        rows = conn.execute("""
            SELECT *
            FROM gateways
            WHERE site_id = ?
            ORDER BY name
        """, (site_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT *
            FROM gateways
            ORDER BY name
        """).fetchall()

    result = []

    for row in rows:
        gateway_id = row["gateway_id"]

        try:
            connection_stats = ttn_get_gateway_connection_stats(gateway_id)

            if connection_stats:
                connection_status = "online"

                last_seen = (
                    connection_stats.get("last_status_received_at")
                    or connection_stats.get("last_uplink_received_at")
                    or connection_stats.get("connected_at")
                )

                protocol = connection_stats.get("protocol")
                last_status_received_at = connection_stats.get("last_status_received_at")
                last_uplink_received_at = connection_stats.get("last_uplink_received_at")
                last_downlink_received_at = connection_stats.get("last_downlink_received_at")
                uplink_count = connection_stats.get("uplink_count")
                downlink_count = connection_stats.get("downlink_count")

                ip = None

                remote_address = connection_stats.get("gateway_remote_address")
                if remote_address:
                    ip = remote_address.get("ip")

                if not ip:
                    last_status = connection_stats.get("last_status", {})
                    ip_list = last_status.get("ip", [])
                    if ip_list:
                        ip = ip_list[0]

                error_message = None

            else:
                connection_status = "offline"
                last_seen = None
                protocol = None
                last_status_received_at = None
                last_uplink_received_at = None
                last_downlink_received_at = None
                uplink_count = 0
                downlink_count = 0
                ip = None
                error_message = None

        except HTTPException as e:
            connection_status = "error"
            last_seen = None
            protocol = None
            last_status_received_at = None
            last_uplink_received_at = None
            last_downlink_received_at = None
            uplink_count = 0
            downlink_count = 0
            ip = None
            error_message = str(e.detail)

        conn.execute("""
            UPDATE gateways
            SET status = ?,
                last_seen = ?
            WHERE gateway_id = ?
        """, (
            connection_status,
            last_seen,
            gateway_id
        ))

        result.append({
            "id": row["id"],
            "gateway_id": gateway_id,
            "name": row["name"],
            "client_id": row["client_id"],
            "site_id": row["site_id"],
            "connection_status": connection_status,
            "last_seen": last_seen,
            "last_status_received_at": last_status_received_at,
            "last_uplink_received_at": last_uplink_received_at,
            "last_downlink_received_at": last_downlink_received_at,
            "uplink_count": uplink_count,
            "downlink_count": downlink_count,
            "protocol": protocol,
            "ip": ip,
            "error_message": error_message
        })

    conn.commit()
    conn.close()

    return result

@router.post("/gateways")
def create_gateway(data: dict):
    gateway_id = data.get("gateway_id", "").strip()
    name = data.get("name", "").strip()

    if not gateway_id:
        raise HTTPException(status_code=400, detail="gateway_id is required")

    if not name:
        name = gateway_id

    client_id = data.get("client_id")
    site_id = data.get("site_id")
    building_id = data.get("building_id")
    floor_id = data.get("floor_id")
    x = data.get("x")
    y = data.get("y")
    label = data.get("label")
    location_note = data.get("location_note")

    conn = db()

    existing = conn.execute("""
        SELECT *
        FROM gateways
        WHERE gateway_id = ?
    """, (gateway_id,)).fetchone()

    if existing:
        old_gateway = dict(existing)

        conn.execute("""
            UPDATE gateways
            SET
                name = ?,
                client_id = ?,
                site_id = ?,
                building_id = ?,
                floor_id = ?,
                x = ?,
                y = ?,
                label = ?,
                location_note = ?
            WHERE gateway_id = ?
        """, (
            name,
            client_id,
            site_id,
            building_id,
            floor_id,
            x,
            y,
            label,
            location_note,
            gateway_id,
        ))

        conn.commit()

        updated = conn.execute("""
            SELECT *
            FROM gateways
            WHERE gateway_id = ?
        """, (gateway_id,)).fetchone()

        log_audit_event(
            conn,
            action="update_gateway",
            target_type="gateway",
            target_id=updated["id"],
            details={
                "old": old_gateway,
                "new": dict(updated)
            }
        )

        conn.close()

        return {
            "status": "updated",
            "gateway": dict(updated)
        }

    cur = conn.execute("""
        INSERT INTO gateways(
            gateway_id,
            name,
            client_id,
            site_id,
            building_id,
            floor_id,
            x,
            y,
            label,
            location_note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        gateway_id,
        name,
        client_id,
        site_id,
        building_id,
        floor_id,
        x,
        y,
        label,
        location_note,
    ))

    conn.commit()

    gateway_db_id = cur.lastrowid

    created = conn.execute("""
        SELECT *
        FROM gateways
        WHERE id = ?
    """, (gateway_db_id,)).fetchone()

    log_audit_event(
        conn,
        action="create_gateway",
        target_type="gateway",
        target_id=gateway_db_id,
        details={
            "gateway": dict(created)
        }
    )

    conn.close()

    return {
        "status": "created",
        "gateway": dict(created)
    }

@router.get("/gateways")
def get_gateways(site_id: int | None = None):
    conn = db()

    if site_id is not None:
        rows = conn.execute("""
            SELECT *
            FROM gateways
            WHERE site_id = ?
            ORDER BY name
        """, (site_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT *
            FROM gateways
            ORDER BY name
        """).fetchall()

    conn.close()

    return [dict(r) for r in rows] 

@router.delete("/gateways/{gateway_db_id}")
def delete_gateway(gateway_db_id: int):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM gateways
        WHERE id = ?
    """, (gateway_db_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Gateway not found"
        )

    conn.execute("""
        DELETE FROM gateways
        WHERE id = ?
    """, (gateway_db_id,))

    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "deleted_gateway": dict(row)
    }

@router.put("/gateways/{gateway_db_id}")
def update_gateway(gateway_db_id: int, data: dict):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM gateways
        WHERE id = ?
    """, (gateway_db_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Gateway not found")

    old_gateway = dict(row)

    name = data.get("name", row["name"])
    gateway_id = data.get("gateway_id", row["gateway_id"])
    client_id = data.get("client_id", row["client_id"])
    site_id = data.get("site_id", row["site_id"])
    building_id = data.get("building_id", row["building_id"])
    floor_id = data.get("floor_id", row["floor_id"])
    x = data.get("x", row["x"])
    y = data.get("y", row["y"])
    label = data.get("label", row["label"])
    location_note = data.get("location_note", row["location_note"])

    conn.execute("""
        UPDATE gateways
        SET gateway_id = ?,
            name = ?,
            client_id = ?,
            site_id = ?,
            building_id = ?,
            floor_id = ?,
            x = ?,
            y = ?,
            label = ?,
            location_note = ?
        WHERE id = ?
    """, (
        gateway_id,
        name,
        client_id,
        site_id,
        building_id,
        floor_id,
        x,
        y,
        label,
        location_note,
        gateway_db_id
    ))

    conn.commit()

    updated = conn.execute("""
        SELECT *
        FROM gateways
        WHERE id = ?
    """, (gateway_db_id,)).fetchone()

    new_gateway = dict(updated)

    tracked_fields = [
        "gateway_id",
        "name",
        "client_id",
        "site_id",
        "building_id",
        "floor_id",
        "x",
        "y",
        "label",
        "location_note"
    ]

    changed_fields = {}

    for field in tracked_fields:
        if old_gateway.get(field) != new_gateway.get(field):
            changed_fields[field] = {
                "old": old_gateway.get(field),
                "new": new_gateway.get(field)
            }

    if changed_fields:
        action_name = "update_gateway"

        if "x" in changed_fields or "y" in changed_fields:
            action_name = "move_gateway"

        log_audit_event(
            conn,
            action=action_name,
            target_type="gateway",
            target_id=gateway_db_id,
            details={
                "changed_fields": changed_fields,
                "old": old_gateway,
                "new": new_gateway
            },
            client_id=new_gateway.get("client_id"),
            site_id=new_gateway.get("site_id"),
            building_id=new_gateway.get("building_id"),
            floor_id=new_gateway.get("floor_id"),
            gateway_id=new_gateway.get("gateway_id")
        )

    conn.close()

    return {
        "status": "updated" if changed_fields else "no_change",
        "gateway": new_gateway,
        "changed_fields": changed_fields
    }

@router.post("/floors/{floor_id}/upload-image")
async def upload_floor_image(
    floor_id: int,
    image: UploadFile = File(...)
):
    conn = db()

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (floor_id,)).fetchone()

    if not floor:
        conn.close()
        raise HTTPException(status_code=404, detail="Floor not found")

    filename = image.filename.replace(" ", "_")

    save_path = f"uploads/floor_{floor_id}_{filename}"

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    from PIL import Image

    img = Image.open(save_path)

    width, height = img.size

    image_path = "/" + save_path

    conn.execute("""
        UPDATE floors
        SET image_path = ?,
            image_width = ?,
            image_height = ?
        WHERE id = ?
    """, (
        image_path,
        width,
        height,
        floor_id,
    ))

    conn.commit()
    conn.close()

    return {
        "status": "uploaded",
        "floor_id": floor_id,
        "image_path": image_path,
        "image_width": width,
        "image_height": height,
    }

@router.get("/sensor-profiles")
def sensor_profiles_api(
    include_disabled: bool = True,
):
    """
    Return all sensor-profile summaries.

    The full TTN formatter is intentionally excluded from this
    lightweight list endpoint.
    """

    conn = db()

    try:
        profiles = list_sensor_profile_summaries(
            conn,
            include_disabled=include_disabled,
        )

        return {
            "status": "ok",
            "count": len(profiles),
            "profiles": profiles,
        }

    finally:
        conn.close()

@router.get("/sensor-profiles/system/status")
def sensor_profile_system_status_api():
    """
    Return database counts for the profile-driven architecture.
    """

    conn = db()

    try:
        profile_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM sensor_profiles
            """
        ).fetchone()["total"]

        active_profile_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM sensor_profiles
            WHERE enabled = 1
              AND status = 'active'
            """
        ).fetchone()["total"]

        sensor_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM sensor_catalog
            """
        ).fetchone()["total"]

        firmware_module_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM firmware_modules
            """
        ).fetchone()["total"]

        telemetry_field_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM sensor_profile_fields
            """
        ).fetchone()["total"]

        alarm_rule_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM sensor_profile_rules
            """
        ).fetchone()["total"]

        assigned_device_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM devices
            WHERE profile_id IS NOT NULL
               OR profile_code IS NOT NULL
            """
        ).fetchone()["total"]

        configuration_history_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM device_configuration_history
            """
        ).fetchone()["total"]

        return {
            "status": "ok",
            "profile_count": profile_count,
            "active_profile_count": active_profile_count,
            "sensor_count": sensor_count,
            "firmware_module_count": firmware_module_count,
            "telemetry_field_count": telemetry_field_count,
            "alarm_rule_count": alarm_rule_count,
            "assigned_device_count": assigned_device_count,
            "configuration_history_count": (
                configuration_history_count
            ),
        }

    finally:
        conn.close()

@router.post("/sensor-profiles/validate")
def validate_sensor_profile_api(
    profile_definition: dict,
):
    """
    Validate a profile definition without saving it.
    """

    conn = db()

    try:
        profile_id = profile_definition.get("id")

        if profile_id is not None:
            try:
                profile_id = int(profile_id)
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Profile id must be an integer",
                )

        result = validate_sensor_profile_definition(
            conn,
            profile_definition,
            exclude_profile_id=profile_id,
        )

        return {
            "status": (
                "valid"
                if result["valid"]
                else "invalid"
            ),
            "valid": result["valid"],
            "errors": result["errors"],
            "schema_checksum": result[
                "schema_checksum"
            ],
            "normalized": result["normalized"],
        }

    finally:
        conn.close()

@router.get("/sensor-profiles/by-code/{profile_code}")
def sensor_profile_detail_by_code_api(
    profile_code: str,
    include_formatter: bool = False,
):
    """
    Return one complete profile using its profile code.
    """

    conn = db()

    try:
        profile = get_sensor_profile_detail(
            conn,
            profile_code,
            include_formatter=include_formatter,
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Sensor profile not found: "
                    + profile_code
                ),
            )

        return {
            "status": "ok",
            "profile": profile,
        }

    finally:
        conn.close()

@router.get("/sensor-profiles/{profile_id}")
def sensor_profile_detail_by_id_api(
    profile_id: int,
    include_formatter: bool = False,
):
    """
    Return one complete profile using its numeric database ID.
    """

    conn = db()

    try:
        profile = get_sensor_profile_detail(
            conn,
            profile_id,
            include_formatter=include_formatter,
        )

        if not profile:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Sensor profile not found with id "
                    + str(profile_id)
                ),
            )

        return {
            "status": "ok",
            "profile": profile,
        }

    finally:
        conn.close()

@router.get("/sensor-catalog")
def sensor_catalog_api(
    include_disabled: bool = True,
):
    """
    Return physical and compatibility sensors registered in
    the sensor catalog.
    """

    conn = db()

    try:
        sql = """
            SELECT
                catalog.id,
                catalog.sensor_code,
                catalog.manufacturer,
                catalog.model,
                catalog.use_case,
                catalog.protocol,
                catalog.default_bus,
                catalog.default_address,
                catalog.datasheet_url,
                catalog.description,
                catalog.enabled,
                catalog.created_at,
                catalog.updated_at,

                COUNT(
                    DISTINCT relation.profile_id
                ) AS profile_count

            FROM sensor_catalog catalog

            LEFT JOIN sensor_profile_sensors relation
                ON relation.sensor_id = catalog.id
        """

        parameters = []

        if not include_disabled:
            sql += """
                WHERE catalog.enabled = 1
            """

        sql += """
            GROUP BY catalog.id

            ORDER BY
                catalog.use_case,
                catalog.manufacturer,
                catalog.model
        """

        rows = conn.execute(
            sql,
            parameters,
        ).fetchall()

        sensors = []

        for row in rows:
            sensor = dict(row)
            sensor["enabled"] = bool(
                sensor.get("enabled")
            )
            sensors.append(sensor)

        return {
            "status": "ok",
            "count": len(sensors),
            "sensors": sensors,
        }

    finally:
        conn.close()

@router.get("/firmware-modules")
def firmware_modules_api(
    include_disabled: bool = True,
):
    """
    Return the firmware drivers/modules supported by profiles.
    """

    conn = db()

    try:
        sql = """
            SELECT
                module.id,
                module.module_key,
                module.display_name,
                module.driver_class,
                module.protocol,
                module.library_name,
                module.library_version,
                module.supported_board,
                module.min_firmware_version,
                module.source_file,
                module.notes,
                module.enabled,
                module.created_at,
                module.updated_at,

                COUNT(
                    DISTINCT relation.profile_id
                ) AS profile_count

            FROM firmware_modules module

            LEFT JOIN sensor_profile_sensors relation
                ON relation.firmware_module_id = module.id
        """

        parameters = []

        if not include_disabled:
            sql += """
                WHERE module.enabled = 1
            """

        sql += """
            GROUP BY module.id

            ORDER BY module.display_name
        """

        rows = conn.execute(
            sql,
            parameters,
        ).fetchall()

        modules = []

        for row in rows:
            module = dict(row)
            module["enabled"] = bool(
                module.get("enabled")
            )

            profile_rows = conn.execute(
                """
                SELECT DISTINCT profile_id
                FROM (
                    SELECT profile_id
                    FROM sensor_profile_sensors
                    WHERE firmware_module_id = ?

                    UNION

                    SELECT profile_id
                    FROM profile_firmware_compatibility
                    WHERE firmware_module_id = ?
                )
                """,
                (module["id"], module["id"]),
            ).fetchall()

            module["profile_count"] = len(profile_rows)
            module["can_delete"] = (
                module["profile_count"] == 0
            )

            modules.append(module)

        return {
            "status": "ok",
            "count": len(modules),
            "modules": modules,
        }

    finally:
        conn.close()

@router.get("/sensor-catalog/{sensor_id}")
def sensor_catalog_detail_api(sensor_id: int):
    """Return one physical sensor catalog record."""

    conn = db()

    try:
        sensor = get_sensor_catalog_detail(
            conn,
            sensor_id,
        )

        if not sensor:
            raise HTTPException(
                status_code=404,
                detail="Sensor catalog record not found",
            )

        return {
            "status": "ok",
            "sensor": sensor,
        }

    finally:
        conn.close()

@router.post(
    "/sensor-catalog",
    status_code=201,
)
def create_sensor_catalog_api(
    request: Request,
    sensor_definition: dict,
):
    """Create a physical sensor catalog record from Admin Portal."""

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(request)

        normalized = normalize_sensor_catalog_definition(
            conn,
            sensor_definition,
        )

        now = profile_utc_now_iso()

        cursor = conn.execute(
            """
            INSERT INTO sensor_catalog(
                sensor_code,
                manufacturer,
                model,
                use_case,
                protocol,
                default_bus,
                default_address,
                datasheet_url,
                description,
                enabled,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized["sensor_code"],
                normalized["manufacturer"],
                normalized["model"],
                normalized["use_case"],
                normalized["protocol"],
                normalized["default_bus"],
                normalized["default_address"],
                normalized["datasheet_url"],
                normalized["description"],
                int(normalized["enabled"]),
                now,
                now,
            ),
        )

        sensor_id = int(cursor.lastrowid)
        conn.commit()

        sensor = get_sensor_catalog_detail(
            conn,
            sensor_id,
        )

        log_audit_event(
            conn,
            action="create_sensor_catalog",
            actor=actor,
            target_type="sensor_catalog",
            target_id=sensor_id,
            details={"sensor": sensor},
            message=(
                "Sensor catalog record created: "
                + normalized["sensor_code"]
            ),
        )

        return {
            "status": "created",
            "message": "Sensor catalog record created",
            "sensor": sensor,
        }

    except ValueError as error:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "The sensor code already exists or conflicts with "
                "another catalog record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()
        print("Create sensor catalog error:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not create the sensor catalog record",
        )

    finally:
        conn.close()

@router.put("/sensor-catalog/{sensor_id}")
def update_sensor_catalog_api(
    sensor_id: int,
    request: Request,
    sensor_definition: dict,
):
    """Update one physical sensor catalog record."""

    conn = db()

    try:
        existing = get_sensor_catalog_detail(
            conn,
            sensor_id,
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Sensor catalog record not found",
            )

        actor = sensor_profile_actor_from_request(request)

        normalized = normalize_sensor_catalog_definition(
            conn,
            sensor_definition,
            exclude_sensor_id=sensor_id,
        )

        conn.execute(
            """
            UPDATE sensor_catalog
            SET
                sensor_code = ?,
                manufacturer = ?,
                model = ?,
                use_case = ?,
                protocol = ?,
                default_bus = ?,
                default_address = ?,
                datasheet_url = ?,
                description = ?,
                enabled = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                normalized["sensor_code"],
                normalized["manufacturer"],
                normalized["model"],
                normalized["use_case"],
                normalized["protocol"],
                normalized["default_bus"],
                normalized["default_address"],
                normalized["datasheet_url"],
                normalized["description"],
                int(normalized["enabled"]),
                profile_utc_now_iso(),
                sensor_id,
            ),
        )

        conn.commit()

        sensor = get_sensor_catalog_detail(
            conn,
            sensor_id,
        )

        log_audit_event(
            conn,
            action="update_sensor_catalog",
            actor=actor,
            target_type="sensor_catalog",
            target_id=sensor_id,
            details={
                "old": existing,
                "new": sensor,
            },
            message=(
                "Sensor catalog record updated: "
                + normalized["sensor_code"]
            ),
        )

        return {
            "status": "updated",
            "message": "Sensor catalog record updated",
            "sensor": sensor,
        }

    except ValueError as error:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "The sensor update conflicts with another record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()
        print("Update sensor catalog error:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not update the sensor catalog record",
        )

    finally:
        conn.close()

@router.post("/sensor-catalog/{sensor_id}/enable")
def enable_sensor_catalog_api(
    sensor_id: int,
    request: Request,
):
    return set_sensor_catalog_enabled_api(
        sensor_id,
        request,
        True,
    )

@router.post("/sensor-catalog/{sensor_id}/disable")
def disable_sensor_catalog_api(
    sensor_id: int,
    request: Request,
):
    return set_sensor_catalog_enabled_api(
        sensor_id,
        request,
        False,
    )

@router.delete("/sensor-catalog/{sensor_id}")
def delete_sensor_catalog_api(
    sensor_id: int,
    request: Request,
):
    """Delete an unused physical sensor catalog record."""

    conn = db()

    try:
        sensor = get_sensor_catalog_detail(
            conn,
            sensor_id,
        )

        if not sensor:
            raise HTTPException(
                status_code=404,
                detail="Sensor catalog record not found",
            )

        if not sensor.get("can_delete"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "This sensor is used by one or more profiles. "
                    "Disable it instead of deleting it."
                ),
            )

        actor = sensor_profile_actor_from_request(request)

        conn.execute(
            "DELETE FROM sensor_catalog WHERE id = ?",
            (sensor_id,),
        )

        conn.commit()

        log_audit_event(
            conn,
            action="delete_sensor_catalog",
            actor=actor,
            target_type="sensor_catalog",
            target_id=sensor_id,
            details={"deleted_sensor": sensor},
            message=(
                "Sensor catalog record deleted: "
                + str(sensor.get("sensor_code"))
            ),
        )

        return {
            "status": "deleted",
            "message": "Sensor catalog record deleted",
            "sensor": sensor,
        }

    except HTTPException:
        conn.rollback()
        raise

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "The sensor is still referenced by another record: "
                + str(error)
            ),
        )

    except Exception as error:
        conn.rollback()
        print("Delete sensor catalog error:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not delete the sensor catalog record",
        )

    finally:
        conn.close()

@router.get("/firmware-modules/{module_id}")
def firmware_module_detail_api(module_id: int):
    """Return one registered firmware driver/module."""

    conn = db()

    try:
        module = get_firmware_module_detail(
            conn,
            module_id,
        )

        if not module:
            raise HTTPException(
                status_code=404,
                detail="Firmware module not found",
            )

        return {
            "status": "ok",
            "module": module,
        }

    finally:
        conn.close()

@router.post(
    "/firmware-modules",
    status_code=201,
)
def create_firmware_module_api(
    request: Request,
    module_definition: dict,
):
    """Register a driver already available in a firmware build."""

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(request)

        normalized = normalize_firmware_module_definition(
            conn,
            module_definition,
        )

        now = profile_utc_now_iso()

        cursor = conn.execute(
            """
            INSERT INTO firmware_modules(
                module_key,
                display_name,
                driver_class,
                protocol,
                library_name,
                library_version,
                supported_board,
                min_firmware_version,
                source_file,
                notes,
                enabled,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized["module_key"],
                normalized["display_name"],
                normalized["driver_class"],
                normalized["protocol"],
                normalized["library_name"],
                normalized["library_version"],
                normalized["supported_board"],
                normalized["min_firmware_version"],
                normalized["source_file"],
                normalized["notes"],
                int(normalized["enabled"]),
                now,
                now,
            ),
        )

        module_id = int(cursor.lastrowid)
        conn.commit()

        module = get_firmware_module_detail(
            conn,
            module_id,
        )

        log_audit_event(
            conn,
            action="create_firmware_module",
            actor=actor,
            target_type="firmware_module",
            target_id=module_id,
            details={"module": module},
            message=(
                "Firmware module registered: "
                + normalized["module_key"]
            ),
        )

        return {
            "status": "created",
            "message": "Firmware module registered",
            "module": module,
        }

    except ValueError as error:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "The firmware module conflicts with an existing record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()
        print("Create firmware module error:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not register the firmware module",
        )

    finally:
        conn.close()

@router.put("/firmware-modules/{module_id}")
def update_firmware_module_api(
    module_id: int,
    request: Request,
    module_definition: dict,
):
    """Update one registered firmware module."""

    conn = db()

    try:
        existing = get_firmware_module_detail(
            conn,
            module_id,
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail="Firmware module not found",
            )

        actor = sensor_profile_actor_from_request(request)

        normalized = normalize_firmware_module_definition(
            conn,
            module_definition,
            exclude_module_id=module_id,
        )

        conn.execute(
            """
            UPDATE firmware_modules
            SET
                module_key = ?,
                display_name = ?,
                driver_class = ?,
                protocol = ?,
                library_name = ?,
                library_version = ?,
                supported_board = ?,
                min_firmware_version = ?,
                source_file = ?,
                notes = ?,
                enabled = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                normalized["module_key"],
                normalized["display_name"],
                normalized["driver_class"],
                normalized["protocol"],
                normalized["library_name"],
                normalized["library_version"],
                normalized["supported_board"],
                normalized["min_firmware_version"],
                normalized["source_file"],
                normalized["notes"],
                int(normalized["enabled"]),
                profile_utc_now_iso(),
                module_id,
            ),
        )

        conn.commit()

        module = get_firmware_module_detail(
            conn,
            module_id,
        )

        log_audit_event(
            conn,
            action="update_firmware_module",
            actor=actor,
            target_type="firmware_module",
            target_id=module_id,
            details={
                "old": existing,
                "new": module,
            },
            message=(
                "Firmware module updated: "
                + normalized["module_key"]
            ),
        )

        return {
            "status": "updated",
            "message": "Firmware module updated",
            "module": module,
        }

    except ValueError as error:
        conn.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "The firmware-module update conflicts with another record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()
        print("Update firmware module error:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not update the firmware module",
        )

    finally:
        conn.close()

@router.post("/firmware-modules/{module_id}/enable")
def enable_firmware_module_api(
    module_id: int,
    request: Request,
):
    return set_firmware_module_enabled_api(
        module_id,
        request,
        True,
    )

@router.post("/firmware-modules/{module_id}/disable")
def disable_firmware_module_api(
    module_id: int,
    request: Request,
):
    return set_firmware_module_enabled_api(
        module_id,
        request,
        False,
    )

@router.delete("/firmware-modules/{module_id}")
def delete_firmware_module_api(
    module_id: int,
    request: Request,
):
    """Delete a firmware module only when no profile references it."""

    conn = db()

    try:
        module = get_firmware_module_detail(
            conn,
            module_id,
        )

        if not module:
            raise HTTPException(
                status_code=404,
                detail="Firmware module not found",
            )

        if not module.get("can_delete"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "This firmware module is used by one or more profiles. "
                    "Disable it instead of deleting it."
                ),
            )

        actor = sensor_profile_actor_from_request(request)

        conn.execute(
            "DELETE FROM firmware_modules WHERE id = ?",
            (module_id,),
        )

        conn.commit()

        log_audit_event(
            conn,
            action="delete_firmware_module",
            actor=actor,
            target_type="firmware_module",
            target_id=module_id,
            details={"deleted_module": module},
            message=(
                "Firmware module deleted: "
                + str(module.get("module_key"))
            ),
        )

        return {
            "status": "deleted",
            "message": "Firmware module deleted",
            "module": module,
        }

    except HTTPException:
        conn.rollback()
        raise

    except sqlite3.IntegrityError as error:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "The firmware module is still referenced: "
                + str(error)
            ),
        )

    except Exception as error:
        conn.rollback()
        print("Delete firmware module error:", error)
        raise HTTPException(
            status_code=500,
            detail="Could not delete the firmware module",
        )

    finally:
        conn.close()

@router.post(
    "/sensor-profiles",
    status_code=201,
)
def create_sensor_profile_api(
    request: Request,
    profile_definition: dict,
):
    """
    Create a new editable sensor profile.
    """

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(
            request
        )

        definition = dict(
            profile_definition or {}
        )

        change_note = str(
            definition.pop(
                "change_note",
                "Profile created through API",
            )
        ).strip()

        created_profile = create_sensor_profile_record(
            conn,
            definition,
            actor=actor,
            change_note=change_note,
        )

        conn.commit()

        return {
            "status": "created",
            "message": "Sensor profile created",
            "profile": created_profile,
        }

    except ValueError as error:
        conn.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "The sensor profile conflicts with "
                "an existing database record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        print(
            "Create sensor profile API error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not create the sensor profile"
            ),
        )

    finally:
        conn.close()

@router.put("/sensor-profiles/{profile_id}")
def update_sensor_profile_api(
    profile_id: int,
    request: Request,
    profile_definition: dict,
):
    """
    Update a custom profile and create a new version.

    Seeded system profiles must be cloned before editing.
    """

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(
            request
        )

        definition = dict(
            profile_definition or {}
        )

        change_note = str(
            definition.pop(
                "change_note",
                "Profile updated through API",
            )
        ).strip()

        updated_profile = update_sensor_profile_record(
            conn,
            profile_id,
            definition,
            actor=actor,
            change_note=change_note,
        )

        conn.commit()

        return {
            "status": "updated",
            "message": "Sensor profile updated",
            "profile": updated_profile,
        }

    except ValueError as error:
        conn.rollback()

        error_message = str(error)

        status_code = 404

        if "not found" not in error_message.lower():
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=error_message,
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "The sensor profile update conflicts "
                "with an existing database record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        print(
            "Update sensor profile API error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not update the sensor profile"
            ),
        )

    finally:
        conn.close()

@router.post(
    "/sensor-profiles/{profile_id}/clone",
    status_code=201,
)
def clone_sensor_profile_api(
    profile_id: int,
    request: Request,
    clone_request: dict,
):
    """
    Clone a profile using either the advanced clone workflow
    or the simplified administrator workflow.
    """

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(
            request
        )

        new_profile_name = str(
            clone_request.get(
                "new_profile_name",
                "",
            )
        ).strip()

        if not new_profile_name:
            raise ValueError(
                "new_profile_name is required"
            )

        new_profile_code = str(
            clone_request.get(
                "new_profile_code",
                "",
            )
        ).strip().upper()

        if not new_profile_code:
            new_profile_code = (
                generate_unique_sensor_profile_code(
                    conn,
                    new_profile_name,
                )
            )

        activate = profile_value_to_boolean(
            clone_request.get(
                "activate",
                False,
            ),
            default=False,
        )

        uplink_interval_seconds = (
            clone_request.get(
                "uplink_interval_seconds"
            )
        )

        alarm_thresholds = (
            clone_request.get(
                "alarm_thresholds",
                {},
            )
        )

        cloned_profile = (
            clone_sensor_profile_record(
                conn,
                profile_id,
                new_profile_code,
                new_profile_name,
                actor=actor,
                activate=activate,
                uplink_interval_seconds=(
                    uplink_interval_seconds
                ),
                alarm_thresholds=(
                    alarm_thresholds
                ),
            )
        )

        conn.commit()

        return {
            "status": (
                "created"
                if activate
                else "cloned"
            ),
            "message": (
                "Sensor profile created and activated"
                if activate
                else "Sensor profile cloned"
            ),
            "source_profile_id": profile_id,
            "generated_profile_code": (
                new_profile_code
            ),
            "profile": cloned_profile,
        }

    except ValueError as error:
        conn.rollback()

        error_message = str(error)
        lower_error = error_message.lower()

        if "not found" in lower_error:
            status_code = 404

        elif (
            "already exists" in lower_error
            or "conflicts" in lower_error
        ):
            status_code = 409

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=error_message,
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "The requested profile code already "
                "exists or conflicts with another record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        print(
            "Clone sensor profile API error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not clone the sensor profile"
            ),
        )

    finally:
        conn.close()

@router.post("/sensor-profiles/{profile_id}/enable")
def enable_sensor_profile_api(
    profile_id: int,
    request: Request,
):
    """
    Enable a sensor profile.
    """

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(
            request
        )

        profile = set_sensor_profile_enabled(
            conn,
            profile_id,
            True,
            actor=actor,
        )

        conn.commit()

        return {
            "status": "enabled",
            "message": "Sensor profile enabled",
            "profile": profile,
        }

    except ValueError as error:
        conn.rollback()

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        print(
            "Enable sensor profile API error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not enable the sensor profile"
            ),
        )

    finally:
        conn.close()

@router.post("/sensor-profiles/{profile_id}/disable")
def disable_sensor_profile_api(
    profile_id: int,
    request: Request,
):
    """
    Disable a sensor profile.

    Disabled profiles remain stored for existing devices and
    history but will later be excluded from new provisioning.
    """

    conn = db()

    try:
        actor = sensor_profile_actor_from_request(
            request
        )

        profile = set_sensor_profile_enabled(
            conn,
            profile_id,
            False,
            actor=actor,
        )

        conn.commit()

        return {
            "status": "disabled",
            "message": "Sensor profile disabled",
            "profile": profile,
        }

    except ValueError as error:
        conn.rollback()

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        print(
            "Disable sensor profile API error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not disable the sensor profile"
            ),
        )

    finally:
        conn.close()

@router.delete("/sensor-profiles/{profile_id}")
def delete_sensor_profile_api(
    profile_id: int,
    request: Request,
):
    """
    Delete an unused custom profile.

    System profiles and profiles referenced by devices or
    configuration history cannot be deleted.
    """

    conn = db()

    try:
        # Resolve the user now so authentication information
        # remains available for later audit integration.
        sensor_profile_actor_from_request(request)

        deleted_profile = delete_sensor_profile_record(
            conn,
            profile_id,
        )

        conn.commit()

        return {
            "status": "deleted",
            "message": "Sensor profile deleted",
            "profile": deleted_profile,
        }

    except ValueError as error:
        conn.rollback()

        error_message = str(error)
        lower_error = error_message.lower()

        if "not found" in lower_error:
            status_code = 404

        elif (
            "cannot be deleted" in lower_error
            or "assigned" in lower_error
            or "history" in lower_error
        ):
            status_code = 409

        else:
            status_code = 400

        raise HTTPException(
            status_code=status_code,
            detail=error_message,
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "The profile is still referenced by "
                "another database record: "
                + str(error)
            ),
        )

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        print(
            "Delete sensor profile API error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not delete the sensor profile"
            ),
        )

    finally:
        conn.close()

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
                print(
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

                print(
                    "Profile-driven ThingsBoard sync:",
                    tb_sync_result["status"],
                    tb_sync_result["profile_code"],
                    tb_sync_result[
                        "tb_device_profile_name"
                    ],
                )

            except Exception as exc:
                print(
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

            print(
                "Profile-driven ThingsBoard sync:",
                tb_sync_result["status"],
                tb_sync_result["profile_code"],
                tb_sync_result[
                    "tb_device_profile_name"
                ],
            )

        except Exception as exc:
            print(
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

        print(
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

@router.get("/device-status/{device_id}")
def device_status(device_id: str):
    conn = db()
    row = get_device_metadata_by_device_id(conn, device_id)
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Device not found in backend database")

    telemetry = read_tb_latest_telemetry(device_id)

    return {
        "device_id": row["device_id"],
        "node_type": row["node_type"],
        "building": row["building"],
        "floor": row["floor"],
        "room": row["room"],
        "label": row["label"],
        "x": row["x"],
        "y": row["y"],
        "icon_type": row["icon_type"],
        "telemetry": telemetry,
    }

@router.get("/devices-status")
def devices_status():
    """
    Return every device with profile-driven telemetry metadata and
    a merged ThingsBoard/local telemetry view.
    """

    conn = db()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM devices
            ORDER BY
                COALESCE(label, device_id),
                device_id
            """
        ).fetchall()

        result = []

        for row in rows:
            device = dict(
                row
            )

            device_id = device[
                "device_id"
            ]

            # =================================================
            # 1. LOAD ASSIGNED SENSOR PROFILE
            # =================================================

            profile = (
                load_device_profile_for_live_telemetry(
                    conn,
                    device_id,
                )
            )

            profile_metadata = (
                build_profile_live_metadata(
                    profile
                )
            )

            # =================================================
            # 2. DETERMINE CAPABILITIES
            # =================================================

            if profile_metadata:
                capabilities = (
                    profile_metadata[
                        "capabilities"
                    ]
                )

            else:
                try:
                    capabilities = (
                        get_device_capabilities_list(
                            conn,
                            device_id,
                            device.get(
                                "node_type"
                            ),
                        )
                    )

                except Exception:
                    capabilities = [
                        device.get(
                            "node_type"
                        )
                    ]

            capabilities = [
                capability
                for capability in capabilities
                if capability
            ]

            # =================================================
            # 3. LOAD THINGSBOARD TELEMETRY
            # =================================================

            try:
                tb_telemetry = (
                    read_tb_latest_telemetry(
                        device_id,
                        profile=profile,
                    )
                    or {}
                )

            except Exception as exc:
                print(
                    "ThingsBoard telemetry failed "
                    "in devices-status:",
                    exc,
                )

                tb_telemetry = {}

            # =================================================
            # 4. LOAD LOCAL VALIDATED TELEMETRY
            # =================================================

            try:
                local_telemetry = (
                    get_local_latest_telemetry(
                        conn,
                        device_id,
                    )
                    or {}
                )

            except Exception as exc:
                print(
                    "Local telemetry failed "
                    "in devices-status:",
                    exc,
                )

                local_telemetry = {}

            # =================================================
            # 5. MERGE BOTH TELEMETRY SOURCES
            # =================================================

            telemetry = (
                merge_profile_live_telemetry_sources(
                    tb_telemetry,
                    local_telemetry,
                )
            )

            telemetry_fields = (
                build_profile_live_field_metadata(
                    profile,
                    surface="all",
                )
            )

            display_telemetry = (
                build_profile_display_telemetry(
                    profile,
                    telemetry,
                    surface="dashboard",
                )
            )

            # =================================================
            # 6. BUILD DEVICE RESPONSE
            # =================================================

            result.append(
                {
                    "device_id": device_id,

                    "node_type": (
                        profile.get(
                            "node_type"
                        )
                        if profile
                        else device.get(
                            "node_type"
                        )
                    ),

                    "capabilities": (
                        capabilities
                    ),

                    "profile_assigned": bool(
                        profile
                    ),

                    "profile": (
                        profile_metadata
                    ),

                    "profile_id": (
                        profile.get("id")
                        if profile
                        else device.get(
                            "profile_id"
                        )
                    ),

                    "profile_code": (
                        profile.get(
                            "profile_code"
                        )
                        if profile
                        else device.get(
                            "profile_code"
                        )
                    ),

                    "profile_version": (
                        profile.get(
                            "profile_version"
                        )
                        if profile
                        else device.get(
                            "profile_version"
                        )
                    ),

                    "payload_version": (
                        profile.get(
                            "payload_version"
                        )
                        if profile
                        else device.get(
                            "payload_version"
                        )
                    ),

                    "building": device.get(
                        "building"
                    ),

                    "floor": device.get(
                        "floor"
                    ),

                    "room": device.get(
                        "room"
                    ),

                    "label": device.get(
                        "label"
                    ),

                    "x": device.get("x"),
                    "y": device.get("y"),

                    "icon_type": (
                        profile.get(
                            "icon_type"
                        )
                        if profile
                        and profile.get(
                            "icon_type"
                        )
                        else device.get(
                            "icon_type"
                        )
                    ),

                    "icon_color": (
                        profile.get(
                            "icon_color"
                        )
                        if profile
                        else None
                    ),

                    "client_id": device.get(
                        "client_id"
                    ),

                    "site_id": device.get(
                        "site_id"
                    ),

                    "building_id": device.get(
                        "building_id"
                    ),

                    "floor_id": device.get(
                        "floor_id"
                    ),

                    "room_id": device.get(
                        "room_id"
                    ),

                    "configuration_status": (
                        device.get(
                            "configuration_status"
                        )
                    ),

                    "configuration_checksum": (
                        device.get(
                            "configuration_checksum"
                        )
                    ),

                    # Raw canonical telemetry remains available
                    # for existing portal code.
                    "telemetry": telemetry,

                    # Every field declared in the profile.
                    "telemetry_fields": (
                        telemetry_fields
                    ),

                    # Dashboard-visible fields combined with
                    # current values.
                    "display_telemetry": (
                        display_telemetry
                    ),
                }
            )

        return result

    finally:
        conn.close()

@router.put("/devices/{device_id}/assign-room")
def assign_device_to_room(device_id: str, data: dict):
    room_id = data.get("room_id")
    x = data.get("x")
    y = data.get("y")

    if not room_id:
        raise HTTPException(status_code=400, detail="room_id is required")

    conn = db()

    device = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    room = conn.execute("""
        SELECT *
        FROM rooms
        WHERE id = ?
    """, (room_id,)).fetchone()

    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Room not found")

    device_dict = dict(device)
    room_dict = dict(room)

    room_name = room_dict.get("room_name") or room_dict.get("name") or device_dict.get("room")

    floor_id = room_dict.get("floorplan_id")

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (floor_id,)).fetchone()

    building_name = device_dict.get("building")
    floor_number = device_dict.get("floor")

    if floor:
        floor_dict = dict(floor)
        floor_number = floor_dict.get("floor_number") or floor_dict.get("name") or floor_number

        building = conn.execute("""
            SELECT *
            FROM buildings
            WHERE id = ?
        """, (floor_dict["building_id"],)).fetchone()

        if building:
            building_name = dict(building).get("name") or building_name

    if x is None:
        x = room_dict.get("center_x") or device_dict.get("x")

    if y is None:
        y = room_dict.get("center_y") or device_dict.get("y")

    conn.execute("""
        UPDATE devices
        SET room_id = ?,
            room = ?,
            building = ?,
            floor = ?,
            x = ?,
            y = ?
        WHERE device_id = ?
    """, (
        room_id,
        room_name,
        building_name,
        floor_number,
        x,
        y,
        device_id
    ))

    conn.commit()

    updated = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    conn.close()

    return {
        "status": "assigned",
        "device": dict(updated)
    }

@router.get("/alarms")
def get_alarms(status: str | None = None):
    conn = db()

    query = """
        SELECT *
        FROM alarm_history
    """
    params = []

    if status == "active":
        query += " WHERE acknowledged = 0 AND resolved = 0"
    elif status == "acknowledged":
        query += " WHERE acknowledged = 1 AND resolved = 0"
    elif status == "resolved":
        query += " WHERE resolved = 1"

    query += " ORDER BY triggered_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []

    for row in rows:
        item = dict(row)

        try:
            item["telemetry"] = json.loads(item["telemetry"]) if item["telemetry"] else {}
        except Exception:
            item["telemetry"] = {}

        result.append(item)

    return result

@router.post("/alarms/{alarm_id}/acknowledge")
def acknowledge_alarm(alarm_id: int, data: dict = {}):
    acknowledged_by = data.get("acknowledged_by", "admin")

    conn = db()

    row = conn.execute("""
        SELECT *
        FROM alarm_history
        WHERE id = ?
    """, (alarm_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Alarm not found")

    old_alarm = dict(row)

    conn.execute("""
        UPDATE alarm_history
        SET acknowledged = 1,
            acknowledged_by = ?,
            acknowledged_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (acknowledged_by, alarm_id))

    conn.commit()

    updated_alarm = conn.execute("""
        SELECT *
        FROM alarm_history
        WHERE id = ?
    """, (alarm_id,)).fetchone()

    new_alarm = dict(updated_alarm)

    device_scope = get_device_scope_for_audit(
        conn,
        new_alarm.get("device_id")
    )

    log_audit_event(
        conn,
        action="acknowledge_alarm",
        actor=acknowledged_by,
        target_type="alarm",
        target_id=alarm_id,
        details={
            "old": old_alarm,
            "new": new_alarm
        },
        client_id=device_scope.get("client_id"),
        site_id=device_scope.get("site_id"),
        building_id=device_scope.get("building_id"),
        floor_id=device_scope.get("floor_id"),
        room_id=device_scope.get("room_id"),
        device_id=device_scope.get("device_id")
    )

    conn.close()

    return {
        "status": "acknowledged",
        "alarm_id": alarm_id,
        "acknowledged_by": acknowledged_by,
        "device_scope": device_scope
    }

@router.post("/alarms/{alarm_id}/resolve")
def resolve_alarm(alarm_id: int, data: dict = {}):
    resolved_by = data.get("resolved_by", "admin")

    conn = db()

    row = conn.execute("""
        SELECT *
        FROM alarm_history
        WHERE id = ?
    """, (alarm_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Alarm not found")

    old_alarm = dict(row)

    conn.execute("""
        UPDATE alarm_history
        SET resolved = 1,
            resolved_by = ?,
            resolved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (resolved_by, alarm_id))

    conn.commit()

    updated_alarm = conn.execute("""
        SELECT *
        FROM alarm_history
        WHERE id = ?
    """, (alarm_id,)).fetchone()

    new_alarm = dict(updated_alarm)

    device_scope = get_device_scope_for_audit(
        conn,
        new_alarm.get("device_id")
    )

    log_audit_event(
        conn,
        action="resolve_alarm",
        actor=resolved_by,
        target_type="alarm",
        target_id=alarm_id,
        details={
            "old": old_alarm,
            "new": new_alarm
        },
        client_id=device_scope.get("client_id"),
        site_id=device_scope.get("site_id"),
        building_id=device_scope.get("building_id"),
        floor_id=device_scope.get("floor_id"),
        room_id=device_scope.get("room_id"),
        device_id=device_scope.get("device_id")
    )

    conn.close()

    return {
        "status": "resolved",
        "alarm_id": alarm_id,
        "resolved_by": resolved_by,
        "device_scope": device_scope
    }

@router.post("/floorplans/upload")
async def upload_floorplan(
    building: str = Form(...),
    floor: str = Form(...),
    image: UploadFile = File(...)
):
    file_ext = os.path.splitext(image.filename)[1].lower()

    if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP images are allowed")

    safe_building = re.sub(r"[^a-zA-Z0-9_-]", "_", building)
    safe_floor = re.sub(r"[^a-zA-Z0-9_-]", "_", floor)

    filename = f"{safe_building}_floor_{safe_floor}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await image.read()

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    conn = db()
    cur = conn.execute(
        """
        INSERT INTO floorplans (
            building,
            floor,
            image_path,
            image_width,
            image_height
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            building,
            floor,
            f"/uploads/{filename}",
            width,
            height,
        ),
    )
    conn.commit()
    floorplan_id = cur.lastrowid
    conn.close()

    return {
        "status": "uploaded",
        "floorplan_id": floorplan_id,
        "building": building,
        "floor": floor,
        "image_path": f"/uploads/{filename}",
        "image_width": width,
        "image_height": height,
    }

@router.get("/floorplans")
def get_floorplans():
    conn = db()

    rows = conn.execute("""
        SELECT id, building, floor, image_path, image_width, image_height, created_at
        FROM floorplans
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "building": row["building"],
            "floor": row["floor"],
            "image_path": row["image_path"],
            "image_width": row["image_width"],
            "image_height": row["image_height"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]

@router.post("/rooms")
async def create_room(data: dict):
    required_fields = [
        "floorplan_id",
        "building",
        "floor",
        "room_name",
        "polygon_points",
    ]

    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing field: {field}"
            )

    polygon_points = data["polygon_points"]

    if not isinstance(polygon_points, list) or len(polygon_points) < 3:
        raise HTTPException(
            status_code=400,
            detail="polygon_points must contain at least 3 points"
        )

    try:
        x_values = [p["x"] for p in polygon_points]
        y_values = [p["y"] for p in polygon_points]

        center_x = int(sum(x_values) / len(x_values))
        center_y = int(sum(y_values) / len(y_values))

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid polygon_points format"
        )

    conn = db()

    cur = conn.execute(
        """
        INSERT INTO rooms (
            floorplan_id,
            building,
            floor,
            room_name,
            polygon_points,
            x,
            y
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["floorplan_id"],
            data["building"],
            data["floor"],
            data["room_name"],
            json.dumps(polygon_points),
            center_x,
            center_y,
        ),
    )

    conn.commit()

    room_id = cur.lastrowid

    conn.close()

    return {
        "status": "created",
        "room_id": room_id,
        "building": data["building"],
        "floor": data["floor"],
        "room_name": data["room_name"],
        "polygon_points": polygon_points,
        "x": center_x,
        "y": center_y,
    }

@router.get("/rooms")
def get_rooms(floorplan_id: int | None = None):
    conn = db()

    if floorplan_id is not None:
        rows = conn.execute("""
            SELECT id, floorplan_id, building, floor, room_name, polygon_points, x, y, created_at
            FROM rooms
            WHERE floorplan_id = ?
            ORDER BY id DESC
        """, (floorplan_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, floorplan_id, building, floor, room_name, polygon_points, x, y, created_at
            FROM rooms
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "floorplan_id": row["floorplan_id"],
            "building": row["building"],
            "floor": row["floor"],
            "room_name": row["room_name"],
            "polygon_points": json.loads(row["polygon_points"]),
            "x": row["x"],
            "y": row["y"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]

@router.get("/floor-map-data")
def floor_map_data(building: str, floor: str):
    conn = db()

    floorplan = conn.execute("""
        SELECT id, building, floor, image_path, image_width, image_height
        FROM floorplans
        WHERE building = ?
        AND floor = ?
        ORDER BY id DESC
        LIMIT 1
    """, (building, floor)).fetchone()

    if not floorplan:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Floorplan not found"
        )

    room_rows = conn.execute("""
        SELECT id, room_name, polygon_points, x, y
        FROM rooms
        WHERE building = ?
        AND floor = ?
        ORDER BY room_name
    """, (building, floor)).fetchall()

    device_rows = conn.execute("""
        SELECT
            device_id,
            node_type,
            building,
            floor,
            room,
            label,
            x,
            y,
            icon_type
        FROM devices
        WHERE building = ?
        AND floor = ?
        ORDER BY room, label
    """, (building, floor)).fetchall()

    conn.close()

    rooms = []

    for row in room_rows:
        rooms.append({
            "id": row["id"],
            "room_name": row["room_name"],
            "polygon_points": json.loads(row["polygon_points"]),
            "x": row["x"],
            "y": row["y"],
        })

    devices = []

    for row in device_rows:
        telemetry = read_tb_latest_telemetry(row["device_id"])

        devices.append({
            "device_id": row["device_id"],
            "node_type": row["node_type"],
            "building": row["building"],
            "floor": row["floor"],
            "room": row["room"],
            "label": row["label"],
            "x": row["x"],
            "y": row["y"],
            "icon_type": row["icon_type"],
            "telemetry": telemetry,
        })

    return {
        "building": floorplan["building"],
        "floor": floorplan["floor"],

        "floorplan": {
            "id": floorplan["id"],
            "image_path": floorplan["image_path"],
            "image_width": floorplan["image_width"],
            "image_height": floorplan["image_height"],
        },

        "rooms": rooms,

        "devices": devices,
    }    

@router.delete("/devices/{device_id}")
def delete_device(device_id: str):
    conn = db()

    cur = conn.execute(
        "DELETE FROM devices WHERE device_id = ?",
        (device_id,)
    )

    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "status": "deleted",
        "device_id": device_id
    }

@router.get("/alarm-settings")
def get_alarm_settings():
    conn = db()

    recipients = conn.execute("""
        SELECT id, email, enabled, created_at
        FROM alarm_recipients
        ORDER BY id DESC
    """).fetchall()

    template = conn.execute("""
        SELECT subject_template, body_template
        FROM alarm_email_template
        WHERE id = 1
    """).fetchone()

    conn.close()

    return {
        "recipients": [
            {
                "id": r["id"],
                "email": r["email"],
                "enabled": bool(r["enabled"]),
                "created_at": r["created_at"],
            }
            for r in recipients
        ],
        "template": {
            "subject_template": template["subject_template"],
            "body_template": template["body_template"],
        } if template else None,
    }

@router.post("/alarm-settings/recipients")
def add_alarm_recipient(data: dict):
    if data.get("admin_password") != ADMIN_PASSWORD_2:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    email = data.get("email", "").strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    conn = db()

    conn.execute("""
        INSERT OR IGNORE INTO alarm_recipients (email, enabled)
        VALUES (?, 1)
    """, (email,))

    conn.commit()
    conn.close()

    return {
        "status": "recipient_added",
        "email": email,
    }

@router.delete("/alarm-settings/recipients/{recipient_id}")
def delete_alarm_recipient(recipient_id: int, admin_password: str):
    if admin_password != ADMIN_PASSWORD_2:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    conn = db()

    cur = conn.execute("""
        DELETE FROM alarm_recipients
        WHERE id = ?
    """, (recipient_id,))

    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Recipient not found")

    return {
        "status": "recipient_deleted",
        "recipient_id": recipient_id,
    }

@router.put("/alarm-settings/template")
def update_alarm_template(data: dict):
    if data.get("admin_password") != ADMIN_PASSWORD_2:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    subject_template = data.get("subject_template", "").strip()
    body_template = data.get("body_template", "").strip()

    if not subject_template or not body_template:
        raise HTTPException(status_code=400, detail="Subject and body templates are required")

    conn = db()

    conn.execute("""
        UPDATE alarm_email_template
        SET subject_template = ?,
            body_template = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (subject_template, body_template))

    conn.commit()
    conn.close()

    return {
        "status": "template_updated",
        "subject_template": subject_template,
        "body_template": body_template,
    }

@router.put("/alarm-settings/recipients/{recipient_id}/enabled")
def update_recipient_enabled(recipient_id: int, data: dict):
    if data.get("admin_password") != ADMIN_PASSWORD_2:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    enabled = 1 if data.get("enabled") is True else 0

    conn = db()

    cur = conn.execute("""
        UPDATE alarm_recipients
        SET enabled = ?
        WHERE id = ?
    """, (enabled, recipient_id))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Recipient not found")

    return {
        "status": "recipient_updated",
        "recipient_id": recipient_id,
        "enabled": bool(enabled),
    }

@router.post("/clients")
def create_client(data: dict):
    name = data.get("name", "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Client name required")

    conn = db()

    cur = conn.execute("""
        INSERT INTO clients(name)
        VALUES(?)
    """, (name,))

    conn.commit()

    client_id = cur.lastrowid

    conn.close()

    return {
        "status": "created",
        "client_id": client_id,
        "name": name,
    }

@router.get("/clients")
def get_clients():
    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM clients
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(r) for r in rows]

@router.post("/sites")
def create_site(data: dict):
    client_id = data.get("client_id")
    name = data.get("name", "").strip()

    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")

    if not name:
        raise HTTPException(status_code=400, detail="Site name required")

    conn = db()

    cur = conn.execute("""
        INSERT INTO sites(
            client_id,
            name
        )
        VALUES (?, ?)
    """, (
        client_id,
        name,
    ))

    conn.commit()

    site_id = cur.lastrowid

    conn.close()

    return {
        "status": "created",
        "site_id": site_id,
        "client_id": client_id,
        "name": name,
    }

@router.get("/sites")
def get_sites(client_id: int | None = None):
    conn = db()

    if client_id is not None:
        rows = conn.execute("""
            SELECT *
            FROM sites
            WHERE client_id = ?
            ORDER BY id DESC
        """, (client_id,)).fetchall()

    else:
        rows = conn.execute("""
            SELECT *
            FROM sites
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return [dict(r) for r in rows]

@router.post("/buildings")
def create_building(data: dict):
    site_id = data.get("site_id")
    name = data.get("name", "").strip()

    if not site_id:
        raise HTTPException(status_code=400, detail="site_id required")

    if not name:
        raise HTTPException(status_code=400, detail="Building name required")

    conn = db()

    cur = conn.execute("""
        INSERT INTO buildings(
            site_id,
            name,
            polygon_points,
            x,
            y
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        site_id,
        name,
        json.dumps(data.get("polygon_points", [])),
        data.get("x"),
        data.get("y"),
    ))

    conn.commit()

    building_id = cur.lastrowid

    conn.close()

    return {
        "status": "created",
        "building_id": building_id,
        "site_id": site_id,
        "name": name,
    }

@router.get("/buildings")
def get_buildings(site_id: int | None = None):
    conn = db()

    if site_id is not None:
        rows = conn.execute("""
            SELECT *
            FROM buildings
            WHERE site_id = ?
            ORDER BY id DESC
        """, (site_id,)).fetchall()

    else:
        rows = conn.execute("""
            SELECT *
            FROM buildings
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    result = []

    for r in rows:
        item = dict(r)

        if item.get("polygon_points"):
            item["polygon_points"] = json.loads(item["polygon_points"])
        else:
            item["polygon_points"] = []

        result.append(item)

    return result

@router.post("/floors")
def create_floor(data: dict):
    building_id = data.get("building_id")

    name = data.get("name", "").strip()

    if not building_id:
        raise HTTPException(status_code=400, detail="building_id required")

    if not name:
        raise HTTPException(status_code=400, detail="Floor name required")

    conn = db()

    cur = conn.execute("""
        INSERT INTO floors(
            building_id,
            name,
            floor_number,
            image_path,
            image_width,
            image_height
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        building_id,
        name,
        data.get("floor_number"),
        data.get("image_path"),
        data.get("image_width"),
        data.get("image_height"),
    ))

    conn.commit()

    floor_id = cur.lastrowid

    conn.close()

    return {
        "status": "created",
        "floor_id": floor_id,
        "building_id": building_id,
        "name": name,
    }

@router.get("/floors")
def get_floors(building_id: int | None = None):
    conn = db()

    if building_id is not None:
        rows = conn.execute("""
            SELECT *
            FROM floors
            WHERE building_id = ?
            ORDER BY id DESC
        """, (building_id,)).fetchall()

    else:
        rows = conn.execute("""
            SELECT *
            FROM floors
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return [dict(r) for r in rows]

@router.post("/users")
def create_user(data: dict):
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    role = data.get("role", "client").strip()
    enabled = data.get("enabled", 1)

    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if not email:
        raise HTTPException(status_code=400, detail="email is required")

    conn = db()

    try:
        cur = conn.execute("""
            INSERT INTO users(
                name,
                email,
                role,
                enabled
            )
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            role,
            enabled
        ))

        conn.commit()

        user_id = cur.lastrowid

        row = conn.execute("""
            SELECT *
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        log_audit_event(
            conn,
            action="create_user",
            target_type="user",
            target_id=user_id,
            details={
                "name": name,
                "email": email,
                "role": role,
                "enabled": enabled
            }
        )

        conn.close()

        return {
            "status": "created",
            "user": dict(row)
        }

    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="User email already exists")

@router.get("/users")
def get_users():
    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    result = []

    for row in rows:
        result.append(safe_user_dict(row))

    return result

@router.put("/users/{user_id}")
def update_user(user_id: int, data: dict):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    old_user = dict(row)

    name = data.get("name", row["name"])
    email = data.get("email", row["email"]).strip().lower()
    role = data.get("role", row["role"])
    enabled = data.get("enabled", row["enabled"])

    try:
        conn.execute("""
            UPDATE users
            SET name = ?,
                email = ?,
                role = ?,
                enabled = ?
            WHERE id = ?
        """, (
            name,
            email,
            role,
            enabled,
            user_id
        ))

        conn.commit()

        updated = conn.execute("""
            SELECT *
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        log_audit_event(
            conn,
            action="update_user",
            target_type="user",
            target_id=user_id,
            details={
                "old": old_user,
                "new": dict(updated)
            }
        )

        conn.close()

        return {
            "status": "updated",
            "user": dict(updated)
        }

    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="User email already exists")

@router.post("/users/{user_id}/disable")
def disable_user(user_id: int):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.execute("""
        UPDATE users
        SET enabled = 0
        WHERE id = ?
    """, (user_id,))

    conn.commit()

    log_audit_event(
        conn,
        action="disable_user",
        target_type="user",
        target_id=user_id,
        details={
            "name": row["name"],
            "email": row["email"]
        }
    )

    conn.close()

    return {
        "status": "disabled",
        "user_id": user_id
    }

@router.post("/users/{user_id}/enable")
def enable_user(user_id: int):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.execute("""
        UPDATE users
        SET enabled = 1
        WHERE id = ?
    """, (user_id,))

    conn.commit()

    log_audit_event(
        conn,
        action="enable_user",
        target_type="user",
        target_id=user_id,
        details={
            "name": row["name"],
            "email": row["email"]
        }
    )

    conn.close()

    return {
        "status": "enabled",
        "user_id": user_id
    }

@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    deleted_user = dict(row)

    access_rows = conn.execute("""
        SELECT *
        FROM user_access
        WHERE user_id = ?
    """, (user_id,)).fetchall()

    deleted_access_records = [dict(a) for a in access_rows]

    conn.execute("""
        DELETE FROM user_access
        WHERE user_id = ?
    """, (user_id,))

    conn.execute("""
        DELETE FROM users
        WHERE id = ?
    """, (user_id,))

    conn.commit()

    log_audit_event(
        conn,
        action="delete_user",
        target_type="user",
        target_id=user_id,
        details={
            "deleted_user": deleted_user,
            "deleted_access_records": deleted_access_records
        }
    )

    conn.close()

    return {
        "status": "deleted",
        "user_id": user_id,
        "deleted_access_records": True
    }

@router.post("/user-access")
def create_user_access(data: dict):
    user_id = data.get("user_id")
    client_id = data.get("client_id")
    site_id = data.get("site_id")
    building_id = data.get("building_id")
    floor_id = data.get("floor_id")

    access_level = data.get("access_level", "viewer")

    can_view_devices = data.get("can_view_devices", 1)
    can_view_gateways = data.get("can_view_gateways", 1)
    can_view_alarms = data.get("can_view_alarms", 1)
    can_view_telemetry = data.get("can_view_telemetry", 1)
    can_manage_email_settings = data.get("can_manage_email_settings", 0)

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    if not client_id and not site_id and not building_id and not floor_id:
        raise HTTPException(
            status_code=400,
            detail="At least one access scope is required: client_id, site_id, building_id, or floor_id"
        )

    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    existing = conn.execute("""
        SELECT *
        FROM user_access
        WHERE user_id = ?
          AND IFNULL(client_id, 0) = IFNULL(?, 0)
          AND IFNULL(site_id, 0) = IFNULL(?, 0)
          AND IFNULL(building_id, 0) = IFNULL(?, 0)
          AND IFNULL(floor_id, 0) = IFNULL(?, 0)
    """, (
        user_id,
        client_id,
        site_id,
        building_id,
        floor_id
    )).fetchone()

    if existing:
        conn.close()
        return {
            "status": "already_exists",
            "access": dict(existing)
        }

    cur = conn.execute("""
        INSERT INTO user_access(
            user_id,
            client_id,
            site_id,
            building_id,
            floor_id,
            access_level,
            can_view_devices,
            can_view_gateways,
            can_view_alarms,
            can_view_telemetry,
            can_manage_email_settings
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        client_id,
        site_id,
        building_id,
        floor_id,
        access_level,
        can_view_devices,
        can_view_gateways,
        can_view_alarms,
        can_view_telemetry,
        can_manage_email_settings
    ))

    conn.commit()

    access_id = cur.lastrowid

    row = conn.execute("""
        SELECT *
        FROM user_access
        WHERE id = ?
    """, (access_id,)).fetchone()

    log_audit_event(
        conn,
        action="create_user_access",
        target_type="user_access",
        target_id=access_id,
        details={
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            },
            "access": dict(row)
        }
    )

    conn.close()

    return {
        "status": "created",
        "access": dict(row)
    }

@router.get("/user-access")
def get_all_user_access():
    conn = db()

    rows = conn.execute("""
        SELECT
            ua.*,
            u.name AS user_name,
            u.email AS user_email
        FROM user_access ua
        JOIN users u ON u.id = ua.user_id
        ORDER BY ua.id DESC
    """).fetchall()

    conn.close()

    return [dict(r) for r in rows]

@router.get("/users/{user_id}/access")
def get_user_access(user_id: int):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    rows = conn.execute("""
        SELECT *
        FROM user_access
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return {
        "user": dict(user),
        "access": [dict(r) for r in rows]
    }

@router.put("/user-access/{access_id}")
def update_user_access(access_id: int, data: dict):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM user_access
        WHERE id = ?
    """, (access_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Access record not found")

    old_access = dict(row)

    client_id = data.get("client_id", row["client_id"])
    site_id = data.get("site_id", row["site_id"])
    building_id = data.get("building_id", row["building_id"])
    floor_id = data.get("floor_id", row["floor_id"])

    access_level = data.get("access_level", row["access_level"])

    can_view_devices = data.get("can_view_devices", row["can_view_devices"])
    can_view_gateways = data.get("can_view_gateways", row["can_view_gateways"])
    can_view_alarms = data.get("can_view_alarms", row["can_view_alarms"])
    can_view_telemetry = data.get("can_view_telemetry", row["can_view_telemetry"])
    can_manage_email_settings = data.get(
        "can_manage_email_settings",
        row["can_manage_email_settings"]
    )

    conn.execute("""
        UPDATE user_access
        SET client_id = ?,
            site_id = ?,
            building_id = ?,
            floor_id = ?,
            access_level = ?,
            can_view_devices = ?,
            can_view_gateways = ?,
            can_view_alarms = ?,
            can_view_telemetry = ?,
            can_manage_email_settings = ?
        WHERE id = ?
    """, (
        client_id,
        site_id,
        building_id,
        floor_id,
        access_level,
        can_view_devices,
        can_view_gateways,
        can_view_alarms,
        can_view_telemetry,
        can_manage_email_settings,
        access_id
    ))

    conn.commit()

    updated = conn.execute("""
        SELECT *
        FROM user_access
        WHERE id = ?
    """, (access_id,)).fetchone()

    new_access = dict(updated)

    log_audit_event(
        conn,
        action="update_user_access",
        target_type="user_access",
        target_id=access_id,
        details={
            "old": old_access,
            "new": new_access
        },
        client_id=new_access.get("client_id"),
        site_id=new_access.get("site_id"),
        building_id=new_access.get("building_id"),
        floor_id=new_access.get("floor_id"),
        user_id=new_access.get("user_id")
    )

    conn.close()

    return {
        "status": "updated",
        "access": new_access
    }

@router.delete("/user-access/{access_id}")
def delete_user_access(access_id: int):
    conn = db()

    row = conn.execute("""
        SELECT *
        FROM user_access
        WHERE id = ?
    """, (access_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Access record not found")

    deleted_access = dict(row)

    conn.execute("""
        DELETE FROM user_access
        WHERE id = ?
    """, (access_id,))

    conn.commit()

    log_audit_event(
        conn,
        action="delete_user_access",
        target_type="user_access",
        target_id=access_id,
        details={
            "deleted_access": deleted_access
        }
    )

    conn.close()

    return {
        "status": "deleted",
        "access_id": access_id
    }

@router.put("/users/{user_id}/credentials")
def update_user_credentials(user_id: int, data: dict, request: Request):
    current_user = get_current_user_from_request(request)

    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")

    if (current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    enabled = data.get("enabled")

    conn = db()

    user_row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
    """, (user_id,)).fetchone()

    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    old_user = dict(user_row)

    if (old_user.get("role") or "").lower() != "client":
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="This endpoint is only for client user credentials"
        )

    updates = []
    params = []
    changed_fields = {}

    if name is not None:
        clean_name = str(name).strip()

        if not clean_name:
            conn.close()
            raise HTTPException(status_code=400, detail="Name cannot be empty")

        updates.append("name = ?")
        params.append(clean_name)

        changed_fields["name"] = {
            "old": old_user.get("name"),
            "new": clean_name
        }

    if email is not None:
        clean_email = str(email).strip().lower()

        if not clean_email:
            conn.close()
            raise HTTPException(status_code=400, detail="Email cannot be empty")

        existing_email = conn.execute("""
            SELECT id
            FROM users
            WHERE email = ?
              AND id != ?
            LIMIT 1
        """, (clean_email, user_id)).fetchone()

        if existing_email:
            conn.close()
            raise HTTPException(
                status_code=409,
                detail="Another user already uses this email"
            )

        updates.append("email = ?")
        params.append(clean_email)

        changed_fields["email"] = {
            "old": old_user.get("email"),
            "new": clean_email
        }

    if enabled is not None:
        enabled_value = 1 if enabled in [1, "1", True, "true", "True", "yes", "on"] else 0

        updates.append("enabled = ?")
        params.append(enabled_value)

        changed_fields["enabled"] = {
            "old": old_user.get("enabled"),
            "new": enabled_value
        }

    password_changed = False

    if password is not None and str(password).strip() != "":
        clean_password = str(password)

        if len(clean_password) < 8:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters"
            )

        password_data = create_password_hash(clean_password)

        updates.append("password_salt = ?")
        params.append(password_data["password_salt"])

        updates.append("password_hash = ?")
        params.append(password_data["password_hash"])

        updates.append("password_iterations = ?")
        params.append(password_data["password_iterations"])

        updates.append("password_updated_at = CURRENT_TIMESTAMP")

        password_changed = True

        changed_fields["password"] = {
            "old": "***hidden***",
            "new": "***updated***"
        }

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No credential fields provided")

    params.append(user_id)

    conn.execute(f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE id = ?
    """, params)

    # If password changed or account disabled, revoke old client sessions.
    if password_changed or enabled in [0, "0", False, "false", "False", "no", "off"]:
        conn.execute("""
            UPDATE auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
              AND revoked_at IS NULL
        """, (user_id,))

    conn.commit()

    updated_user_row = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
        LIMIT 1
    """, (user_id,)).fetchone()

    updated_user = safe_user_dict(updated_user_row)

    log_audit_event(
        conn=conn,
        action="update_client_credentials",
        actor=current_user.get("email", "admin"),
        target_type="user",
        target_id=user_id,
        user_id=user_id,
        details={
            "old": {
                "id": old_user.get("id"),
                "name": old_user.get("name"),
                "email": old_user.get("email"),
                "role": old_user.get("role"),
                "enabled": old_user.get("enabled"),
                "password_updated_at": old_user.get("password_updated_at")
            },
            "new": updated_user,
            "changed_fields": changed_fields
        }
    )

    conn.close()

    return {
        "status": "credentials_updated",
        "user": updated_user,
        "changed_fields": changed_fields
    }

@router.get("/client-portal/{user_id}/allowed-floors")
def client_allowed_floors(user_id: int):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] == 0:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    access_rows = get_user_access_rows(conn, user_id)

    allowed_floors = {}

    for access in access_rows:
        query = """
            SELECT
                f.*,
                b.name AS building_name,
                s.name AS site_name,
                c.name AS client_name
            FROM floors f
            LEFT JOIN buildings b ON b.id = f.building_id
            LEFT JOIN sites s ON s.id = b.site_id
            LEFT JOIN clients c ON c.id = s.client_id
            WHERE 1 = 1
        """

        params = []

        if access["floor_id"]:
            query += " AND f.id = ?"
            params.append(access["floor_id"])

        elif access["building_id"]:
            query += " AND f.building_id = ?"
            params.append(access["building_id"])

        elif access["site_id"]:
            query += " AND b.site_id = ?"
            params.append(access["site_id"])

        elif access["client_id"]:
            query += " AND s.client_id = ?"
            params.append(access["client_id"])

        rows = conn.execute(query, params).fetchall()

        for floor in rows:
            item = dict(floor)

            item["permissions"] = {
                "access_id": access["id"],
                "access_level": access["access_level"],
                "can_view_devices": access["can_view_devices"],
                "can_view_gateways": access["can_view_gateways"],
                "can_view_alarms": access["can_view_alarms"],
                "can_view_telemetry": access["can_view_telemetry"],
                "can_manage_email_settings": access["can_manage_email_settings"],
            }

            allowed_floors[item["id"]] = item

    conn.close()

    return {
        "user": dict(user),
        "floors": list(allowed_floors.values())
    }

@router.get("/client-portal/{user_id}/floors/{floor_id}/live")
def client_floor_live(user_id: int, floor_id: int):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] == 0:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    access = user_can_access_floor(conn, user_id, floor_id)

    if not access:
        conn.close()
        raise HTTPException(status_code=403, detail="User does not have access to this floor")

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (floor_id,)).fetchone()

    if not floor:
        conn.close()
        raise HTTPException(status_code=404, detail="Floor not found")

    room_rows = conn.execute("""
       SELECT *
       FROM rooms
       WHERE floor_id = ?
       OR floorplan_id = ?
       ORDER BY room_name
       """, (floor_id, floor_id)).fetchall()

    rooms = []

    for room in room_rows:
        room_dict = dict(room)

        device_rows = conn.execute("""
            SELECT *
            FROM devices
            WHERE room_id = ?
            ORDER BY label
        """, (room["id"],)).fetchall()

        devices = []

        for d in device_rows:
          
          device = dict(d)

          local_telemetry = get_local_latest_telemetry(conn, device["device_id"])

          if local_telemetry:
              
             device["telemetry"] = local_telemetry

          devices.append(device)

        room_dict["devices"] = devices
        rooms.append(room_dict)

    gateways = []

    if access["can_view_gateways"]:
        gateway_rows = conn.execute("""
            SELECT *
            FROM gateways
            WHERE floor_id = ?
            ORDER BY name
        """, (floor_id,)).fetchall()

        gateways = [dict(g) for g in gateway_rows]

    conn.close()

    return {
        "user": dict(user),
        "permissions": {
            "access_level": access["access_level"],
            "can_view_devices": access["can_view_devices"],
            "can_view_gateways": access["can_view_gateways"],
            "can_view_alarms": access["can_view_alarms"],
            "can_view_telemetry": access["can_view_telemetry"],
            "can_manage_email_settings": access["can_manage_email_settings"],
        },
        "floor": dict(floor),
        "rooms": rooms if access["can_view_devices"] else [],
        "gateways": gateways
    }

@router.get("/client-portal/{user_id}/allowed-structure")
def client_allowed_structure(user_id: int):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] == 0:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    access_rows = get_user_access_rows(conn, user_id)

    structure = {}
    added_floor_ids = set()

    for access in access_rows:
        query = """
            SELECT
                c.id AS client_id,
                c.name AS client_name,

                s.id AS site_id,
                s.name AS site_name,

                b.id AS building_id,
                b.name AS building_name,

                f.id AS floor_id,
                f.name AS floor_name,
                f.floor_number AS floor_number,
                f.image_path AS image_path,
                f.image_width AS image_width,
                f.image_height AS image_height
            FROM floors f
            LEFT JOIN buildings b ON b.id = f.building_id
            LEFT JOIN sites s ON s.id = b.site_id
            LEFT JOIN clients c ON c.id = s.client_id
            WHERE 1 = 1
        """

        params = []

        if access["floor_id"]:
            query += " AND f.id = ?"
            params.append(access["floor_id"])

        elif access["building_id"]:
            query += " AND b.id = ?"
            params.append(access["building_id"])

        elif access["site_id"]:
            query += " AND s.id = ?"
            params.append(access["site_id"])

        elif access["client_id"]:
            query += " AND c.id = ?"
            params.append(access["client_id"])

        rows = conn.execute(query, params).fetchall()

        for row in rows:
            r = dict(row)

            client_id = r["client_id"]
            site_id = r["site_id"]
            building_id = r["building_id"]
            floor_id = r["floor_id"]
            if floor_id in added_floor_ids:

                continue

            added_floor_ids.add(floor_id)

            if client_id not in structure:
                structure[client_id] = {
                    "id": client_id,
                    "name": r["client_name"],
                    "sites": {}
                }

            if site_id not in structure[client_id]["sites"]:
                structure[client_id]["sites"][site_id] = {
                    "id": site_id,
                    "name": r["site_name"],
                    "buildings": {}
                }

            if building_id not in structure[client_id]["sites"][site_id]["buildings"]:
                structure[client_id]["sites"][site_id]["buildings"][building_id] = {
                    "id": building_id,
                    "name": r["building_name"],
                    "floors": []
                }

            structure[client_id]["sites"][site_id]["buildings"][building_id]["floors"].append({
                "id": floor_id,
                "name": r["floor_name"],
                "floor_number": r["floor_number"],
                "image_path": r["image_path"],
                "image_width": r["image_width"],
                "image_height": r["image_height"],
                "permissions": {
                    "access_id": access["id"],
                    "access_level": access["access_level"],
                    "can_view_devices": access["can_view_devices"],
                    "can_view_gateways": access["can_view_gateways"],
                    "can_view_alarms": access["can_view_alarms"],
                    "can_view_telemetry": access["can_view_telemetry"],
                    "can_manage_email_settings": access["can_manage_email_settings"],
                }
            })

    final_structure = []

    for client in structure.values():
        sites_list = []

        for site in client["sites"].values():
            buildings_list = []

            for building in site["buildings"].values():
                buildings_list.append(building)

            site["buildings"] = buildings_list
            sites_list.append(site)

        client["sites"] = sites_list
        final_structure.append(client)

    conn.close()

    return {
        "user": dict(user),
        "structure": final_structure
    }

@router.get("/client-portal/{user_id}/devices/{device_id}/latest-telemetry")
def client_device_latest_telemetry(user_id: int, device_id: str):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] == 0:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    device = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    device_dict = dict(device)

    floor_id = device_dict.get("floor_id")

    if not floor_id and device_dict.get("room_id"):
        room = conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
        """, (device_dict["room_id"],)).fetchone()

        if room:
            room_dict = dict(room)
            floor_id = room_dict.get("floor_id") or room_dict.get("floorplan_id")

    if not floor_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Device is not linked to a floor")

    access = user_can_access_floor(conn, user_id, floor_id)

    if not access:
        conn.close()
        raise HTTPException(status_code=403, detail="User does not have access to this device")

    if access["can_view_telemetry"] == 0:
        conn.close()
        raise HTTPException(status_code=403, detail="User is not allowed to view telemetry")

    row = conn.execute("""
        SELECT *
        FROM device_latest_telemetry
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    conn.close()

    if not row:
        return {
            "device_id": device_id,
            "telemetry": {},
            "alarm_active": 0,
            "alarm_message": "No telemetry received yet",
            "updated_at": None
        }

    item = dict(row)

    try:
        telemetry = json.loads(item["telemetry"]) if item["telemetry"] else {}
    except Exception:
        telemetry = {}

    return {
        "device_id": device_id,
        "telemetry": telemetry,
        "alarm_active": item["alarm_active"],
        "alarm_message": item["alarm_message"],
        "updated_at": item["updated_at"]
    }

@router.get("/client-portal/{user_id}/alarms/export.csv")
def client_portal_alarm_history_export_csv(
    user_id: int,
    limit: int = 1000,
    device_id: str = None,
    node_type: str = None,
    alarm_type: str = None,
    acknowledged: int = None,
    resolved: int = None,
    building_id: int = None,
    floor_id: int = None,
    room_id: int = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None
):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] != 1:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    access_rows = conn.execute("""
        SELECT *
        FROM user_access
        WHERE user_id = ?
          AND can_view_alarms = 1
    """, (user_id,)).fetchall()

    if not access_rows:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="User does not have alarm export permission"
        )

    where_clauses = []
    params = []

    scope_clauses = []
    scope_params = []

    for access in access_rows:
        access_client_id = access["client_id"]
        access_site_id = access["site_id"]
        access_building_id = access["building_id"]
        access_floor_id = access["floor_id"]

        if access_floor_id:
            scope_clauses.append("r.floor_id = ?")
            scope_params.append(access_floor_id)

        elif access_building_id:
            scope_clauses.append("f.building_id = ?")
            scope_params.append(access_building_id)

        elif access_site_id:
            scope_clauses.append("b.site_id = ?")
            scope_params.append(access_site_id)

        elif access_client_id:
            scope_clauses.append("s.client_id = ?")
            scope_params.append(access_client_id)

    if not scope_clauses:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="No valid alarm export scope found"
        )

    where_clauses.append("(" + " OR ".join(scope_clauses) + ")")
    params.extend(scope_params)

    def add_alarm_filter(column_name, value):
        if value is not None and value != "":
            where_clauses.append(f"ah.{column_name} = ?")
            params.append(value)

    add_alarm_filter("device_id", device_id)
    add_alarm_filter("node_type", node_type)
    add_alarm_filter("alarm_type", alarm_type)
    add_alarm_filter("acknowledged", acknowledged)
    add_alarm_filter("resolved", resolved)

    if building_id is not None:
        where_clauses.append("f.building_id = ?")
        params.append(building_id)

    if floor_id is not None:
        where_clauses.append("r.floor_id = ?")
        params.append(floor_id)

    if room_id is not None:
        where_clauses.append("d.room_id = ?")
        params.append(room_id)

    if search:
        where_clauses.append("""
            (
                ah.device_id LIKE ?
                OR ah.node_type LIKE ?
                OR ah.building LIKE ?
                OR ah.floor LIKE ?
                OR ah.room LIKE ?
                OR ah.alarm_type LIKE ?
                OR ah.alarm_message LIKE ?
                OR ah.telemetry LIKE ?
            )
        """)

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if from_date:
        where_clauses.append("ah.triggered_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("ah.triggered_at <= ?")

        if len(to_date) == 10:
            params.append(to_date + " 23:59:59")
        else:
            params.append(to_date)

    if limit < 1:
        limit = 1000

    if limit > 5000:
        limit = 5000

    where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = conn.execute(f"""
        SELECT
            ah.*,
            s.client_id AS scope_client_id,
            b.site_id AS scope_site_id,
            f.building_id AS scope_building_id,
            r.floor_id AS scope_floor_id,
            d.room_id AS scope_room_id
        FROM alarm_history ah
        LEFT JOIN devices d ON ah.device_id = d.device_id
        LEFT JOIN rooms r ON d.room_id = r.id
        LEFT JOIN floors f ON r.floor_id = f.id
        LEFT JOIN buildings b ON f.building_id = b.id
        LEFT JOIN sites s ON b.site_id = s.id
        {where_sql}
        ORDER BY datetime(ah.triggered_at) DESC, ah.id DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    output = io.StringIO()

    fieldnames = [
        "id",
        "device_id",
        "node_type",
        "building",
        "floor",
        "room",
        "alarm_type",
        "alarm_message",
        "triggered_at",
        "acknowledged",
        "acknowledged_by",
        "acknowledged_at",
        "resolved",
        "resolved_by",
        "resolved_at",
        "client_id",
        "site_id",
        "building_id",
        "floor_id",
        "room_id",
        "telemetry"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        item = dict(row)

        try:
            telemetry_obj = json.loads(item["telemetry"]) if item.get("telemetry") else {}
            telemetry_text = json.dumps(telemetry_obj, ensure_ascii=False)
        except Exception:
            telemetry_text = item.get("telemetry") or ""

        writer.writerow({
            "id": item.get("id"),
            "device_id": item.get("device_id"),
            "node_type": item.get("node_type"),
            "building": item.get("building"),
            "floor": item.get("floor"),
            "room": item.get("room"),
            "alarm_type": item.get("alarm_type"),
            "alarm_message": item.get("alarm_message"),
            "triggered_at": item.get("triggered_at"),
            "acknowledged": item.get("acknowledged"),
            "acknowledged_by": item.get("acknowledged_by"),
            "acknowledged_at": item.get("acknowledged_at"),
            "resolved": item.get("resolved"),
            "resolved_by": item.get("resolved_by"),
            "resolved_at": item.get("resolved_at"),
            "client_id": item.get("scope_client_id"),
            "site_id": item.get("scope_site_id"),
            "building_id": item.get("scope_building_id"),
            "floor_id": item.get("scope_floor_id"),
            "room_id": item.get("scope_room_id"),
            "telemetry": telemetry_text
        })

    conn.close()

    output.seek(0)

    export_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"client_alarm_history_user_{user_id}_{export_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/client-portal/{user_id}/export/full-structure.csv")
def client_portal_full_structure_export_csv(user_id: int):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] != 1:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    access_rows = conn.execute("""
        SELECT *
        FROM user_access
        WHERE user_id = ?
    """, (user_id,)).fetchall()

    if not access_rows:
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="User has no allowed export scope"
        )

    def rows_to_dicts(query, params=()):
        return [dict(row) for row in conn.execute(query, params).fetchall()]

    def clean_details(data):
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return str(data)

    def get_name(row, keys=("name", "label", "title")):
        if not row:
            return ""

        for key in keys:
            value = row.get(key)
            if value:
                return value

        return ""

    clients = rows_to_dicts("SELECT * FROM clients ORDER BY id")
    sites = rows_to_dicts("SELECT * FROM sites ORDER BY id")
    buildings = rows_to_dicts("SELECT * FROM buildings ORDER BY id")
    floors = rows_to_dicts("SELECT * FROM floors ORDER BY id")
    rooms = rows_to_dicts("SELECT * FROM rooms ORDER BY id")
    devices = rows_to_dicts("SELECT * FROM devices ORDER BY device_id")
    gateways = rows_to_dicts("SELECT * FROM gateways ORDER BY id")

    clients_by_id = {row.get("id"): row for row in clients}
    sites_by_id = {row.get("id"): row for row in sites}
    buildings_by_id = {row.get("id"): row for row in buildings}
    floors_by_id = {row.get("id"): row for row in floors}
    rooms_by_id = {row.get("id"): row for row in rooms}

    allowed_client_ids = set()
    allowed_site_ids = set()
    allowed_building_ids = set()
    allowed_floor_ids = set()
    allowed_room_ids = set()
    allowed_device_ids = set()
    allowed_gateway_ids = set()

    def add_client_scope(client_id):
        if not client_id:
            return

        allowed_client_ids.add(client_id)

        for site in sites:
            if site.get("client_id") == client_id:
                add_site_scope(site.get("id"))

    def add_site_scope(site_id):
        if not site_id:
            return

        allowed_site_ids.add(site_id)

        site = sites_by_id.get(site_id)
        if site and site.get("client_id"):
            allowed_client_ids.add(site.get("client_id"))

        for building in buildings:
            if building.get("site_id") == site_id:
                add_building_scope(building.get("id"))

    def add_building_scope(building_id):
        if not building_id:
            return

        allowed_building_ids.add(building_id)

        building = buildings_by_id.get(building_id)
        if building and building.get("site_id"):
            site_id = building.get("site_id")
            allowed_site_ids.add(site_id)

            site = sites_by_id.get(site_id)
            if site and site.get("client_id"):
                allowed_client_ids.add(site.get("client_id"))

        for floor in floors:
            if floor.get("building_id") == building_id:
                add_floor_scope(floor.get("id"))

    def add_floor_scope(floor_id):
        if not floor_id:
            return

        allowed_floor_ids.add(floor_id)

        floor = floors_by_id.get(floor_id)
        if floor and floor.get("building_id"):
            building_id = floor.get("building_id")
            allowed_building_ids.add(building_id)

            building = buildings_by_id.get(building_id)
            if building and building.get("site_id"):
                site_id = building.get("site_id")
                allowed_site_ids.add(site_id)

                site = sites_by_id.get(site_id)
                if site and site.get("client_id"):
                    allowed_client_ids.add(site.get("client_id"))

        for room in rooms:
            if room.get("floor_id") == floor_id:
                allowed_room_ids.add(room.get("id"))

    def device_is_in_allowed_scope(device):
        room_id = device.get("room_id")

        if room_id and room_id in allowed_room_ids:
            return True

        floor_id = device.get("floor_id")
        if floor_id and floor_id in allowed_floor_ids:
            return True

        building_id = device.get("building_id")
        if building_id and building_id in allowed_building_ids:
            return True

        site_id = device.get("site_id")
        if site_id and site_id in allowed_site_ids:
            return True

        client_id = device.get("client_id")
        if client_id and client_id in allowed_client_ids:
            return True

        if room_id:
            room = rooms_by_id.get(room_id)
            if room and room.get("floor_id") in allowed_floor_ids:
                return True

        return False

    def gateway_is_in_allowed_scope(gateway):
        floor_id = gateway.get("floor_id")

        if floor_id and floor_id in allowed_floor_ids:
            return True

        building_id = gateway.get("building_id")
        if building_id and building_id in allowed_building_ids:
            return True

        site_id = gateway.get("site_id")
        if site_id and site_id in allowed_site_ids:
            return True

        client_id = gateway.get("client_id")
        if client_id and client_id in allowed_client_ids:
            return True

        if floor_id:
            floor = floors_by_id.get(floor_id)
            if floor and floor.get("building_id") in allowed_building_ids:
                return True

        return False

    for access in access_rows:
        if access["floor_id"]:
            add_floor_scope(access["floor_id"])

        elif access["building_id"]:
            add_building_scope(access["building_id"])

        elif access["site_id"]:
            add_site_scope(access["site_id"])

        elif access["client_id"]:
            add_client_scope(access["client_id"])

    for access in access_rows:
        can_view_devices = access["can_view_devices"] == 1
        can_view_gateways = access["can_view_gateways"] == 1

        temp_client_ids = set()
        temp_site_ids = set()
        temp_building_ids = set()
        temp_floor_ids = set()
        temp_room_ids = set()

        if access["floor_id"]:
            temp_floor_ids.add(access["floor_id"])

        elif access["building_id"]:
            temp_building_ids.add(access["building_id"])

            for floor in floors:
                if floor.get("building_id") == access["building_id"]:
                    temp_floor_ids.add(floor.get("id"))

        elif access["site_id"]:
            temp_site_ids.add(access["site_id"])

            for building in buildings:
                if building.get("site_id") == access["site_id"]:
                    temp_building_ids.add(building.get("id"))

            for floor in floors:
                if floor.get("building_id") in temp_building_ids:
                    temp_floor_ids.add(floor.get("id"))

        elif access["client_id"]:
            temp_client_ids.add(access["client_id"])

            for site in sites:
                if site.get("client_id") == access["client_id"]:
                    temp_site_ids.add(site.get("id"))

            for building in buildings:
                if building.get("site_id") in temp_site_ids:
                    temp_building_ids.add(building.get("id"))

            for floor in floors:
                if floor.get("building_id") in temp_building_ids:
                    temp_floor_ids.add(floor.get("id"))

        for room in rooms:
            if room.get("floor_id") in temp_floor_ids:
                temp_room_ids.add(room.get("id"))

        if can_view_devices:
            for device in devices:
                device_room_id = device.get("room_id")
                device_floor_id = device.get("floor_id")
                device_building_id = device.get("building_id")
                device_site_id = device.get("site_id")
                device_client_id = device.get("client_id")

                if (
                    device_room_id in temp_room_ids
                    or device_floor_id in temp_floor_ids
                    or device_building_id in temp_building_ids
                    or device_site_id in temp_site_ids
                    or device_client_id in temp_client_ids
                ):
                    allowed_device_ids.add(device.get("device_id"))

        if can_view_gateways:
            for gateway in gateways:
                gateway_floor_id = gateway.get("floor_id")
                gateway_building_id = gateway.get("building_id")
                gateway_site_id = gateway.get("site_id")
                gateway_client_id = gateway.get("client_id")

                if (
                    gateway_floor_id in temp_floor_ids
                    or gateway_building_id in temp_building_ids
                    or gateway_site_id in temp_site_ids
                    or gateway_client_id in temp_client_ids
                ):
                    allowed_gateway_ids.add(gateway.get("gateway_id"))

    output = io.StringIO()

    fieldnames = [
        "record_type",
        "client_id",
        "client_name",
        "site_id",
        "site_name",
        "building_id",
        "building_name",
        "floor_id",
        "floor_name",
        "floor_number",
        "room_id",
        "room_name",
        "asset_type",
        "asset_id",
        "asset_name",
        "device_id",
        "gateway_id",
        "node_type",
        "status",
        "x",
        "y",
        "label",
        "location_note",
        "last_seen",
        "created_at",
        "details"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    def write_row(
        record_type,
        client=None,
        site=None,
        building=None,
        floor=None,
        room=None,
        asset_type="",
        asset_id="",
        asset_name="",
        device_id="",
        gateway_id="",
        node_type="",
        status="",
        x="",
        y="",
        label="",
        location_note="",
        last_seen="",
        created_at="",
        details=None
    ):
        writer.writerow({
            "record_type": record_type,

            "client_id": client.get("id") if client else "",
            "client_name": get_name(client),

            "site_id": site.get("id") if site else "",
            "site_name": get_name(site),

            "building_id": building.get("id") if building else "",
            "building_name": get_name(building),

            "floor_id": floor.get("id") if floor else "",
            "floor_name": get_name(floor),
            "floor_number": floor.get("floor_number") if floor else "",

            "room_id": room.get("id") if room else "",
            "room_name": get_name(room),

            "asset_type": asset_type,
            "asset_id": asset_id,
            "asset_name": asset_name,
            "device_id": device_id,
            "gateway_id": gateway_id,
            "node_type": node_type,
            "status": status,
            "x": x,
            "y": y,
            "label": label,
            "location_note": location_note,
            "last_seen": last_seen,
            "created_at": created_at,
            "details": clean_details(details or {})
        })

    for client in clients:
        if client.get("id") not in allowed_client_ids:
            continue

        write_row(
            record_type="CLIENT",
            client=client,
            asset_type="client",
            asset_id=client.get("id"),
            asset_name=get_name(client),
            created_at=client.get("created_at", ""),
            details=client
        )

    for site in sites:
        if site.get("id") not in allowed_site_ids:
            continue

        client = clients_by_id.get(site.get("client_id"))

        write_row(
            record_type="SITE",
            client=client,
            site=site,
            asset_type="site",
            asset_id=site.get("id"),
            asset_name=get_name(site),
            created_at=site.get("created_at", ""),
            details=site
        )

    for building in buildings:
        if building.get("id") not in allowed_building_ids:
            continue

        site = sites_by_id.get(building.get("site_id"))
        client = clients_by_id.get(site.get("client_id")) if site else None

        write_row(
            record_type="BUILDING",
            client=client,
            site=site,
            building=building,
            asset_type="building",
            asset_id=building.get("id"),
            asset_name=get_name(building),
            created_at=building.get("created_at", ""),
            details=building
        )

    for floor in floors:
        if floor.get("id") not in allowed_floor_ids:
            continue

        building = buildings_by_id.get(floor.get("building_id"))
        site = sites_by_id.get(building.get("site_id")) if building else None
        client = clients_by_id.get(site.get("client_id")) if site else None

        write_row(
            record_type="FLOOR",
            client=client,
            site=site,
            building=building,
            floor=floor,
            asset_type="floor",
            asset_id=floor.get("id"),
            asset_name=get_name(floor),
            created_at=floor.get("created_at", ""),
            details=floor
        )

    for room in rooms:
        if room.get("id") not in allowed_room_ids:
            continue

        floor = floors_by_id.get(room.get("floor_id"))
        building = buildings_by_id.get(floor.get("building_id")) if floor else None
        site = sites_by_id.get(building.get("site_id")) if building else None
        client = clients_by_id.get(site.get("client_id")) if site else None

        write_row(
            record_type="ROOM",
            client=client,
            site=site,
            building=building,
            floor=floor,
            room=room,
            asset_type="room",
            asset_id=room.get("id"),
            asset_name=get_name(room),
            x=room.get("x", ""),
            y=room.get("y", ""),
            created_at=room.get("created_at", ""),
            details=room
        )

    for device in devices:
        if device.get("device_id") not in allowed_device_ids:
            continue

        room = rooms_by_id.get(device.get("room_id"))
        floor = floors_by_id.get(room.get("floor_id")) if room else floors_by_id.get(device.get("floor_id"))
        building = buildings_by_id.get(floor.get("building_id")) if floor else buildings_by_id.get(device.get("building_id"))
        site = sites_by_id.get(building.get("site_id")) if building else sites_by_id.get(device.get("site_id"))
        client = clients_by_id.get(site.get("client_id")) if site else clients_by_id.get(device.get("client_id"))

        write_row(
            record_type="DEVICE",
            client=client,
            site=site,
            building=building,
            floor=floor,
            room=room,
            asset_type="device",
            asset_id=device.get("device_id"),
            asset_name=device.get("label") or device.get("device_id"),
            device_id=device.get("device_id"),
            node_type=device.get("node_type", ""),
            status=device.get("status", ""),
            x=device.get("x", ""),
            y=device.get("y", ""),
            label=device.get("label", ""),
            last_seen=device.get("last_seen", ""),
            created_at=device.get("created_at", ""),
            details=device
        )

    for gateway in gateways:
        if gateway.get("gateway_id") not in allowed_gateway_ids:
            continue

        floor = floors_by_id.get(gateway.get("floor_id"))
        building = buildings_by_id.get(gateway.get("building_id")) or (
            buildings_by_id.get(floor.get("building_id")) if floor else None
        )
        site = sites_by_id.get(gateway.get("site_id")) or (
            sites_by_id.get(building.get("site_id")) if building else None
        )
        client = clients_by_id.get(gateway.get("client_id")) or (
            clients_by_id.get(site.get("client_id")) if site else None
        )

        write_row(
            record_type="GATEWAY",
            client=client,
            site=site,
            building=building,
            floor=floor,
            room=None,
            asset_type="gateway",
            asset_id=gateway.get("gateway_id"),
            asset_name=gateway.get("label") or gateway.get("name") or gateway.get("gateway_id"),
            gateway_id=gateway.get("gateway_id"),
            status=gateway.get("status", ""),
            x=gateway.get("x", ""),
            y=gateway.get("y", ""),
            label=gateway.get("label", ""),
            location_note=gateway.get("location_note", ""),
            last_seen=gateway.get("last_seen", ""),
            created_at=gateway.get("created_at", ""),
            details=gateway
        )

    conn.close()

    output.seek(0)

    export_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"client_full_structure_user_{user_id}_{export_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/devices/{device_id}/latest-telemetry")
def admin_device_latest_telemetry(device_id: str):
    conn = db()

    device = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")

    row = conn.execute("""
        SELECT *
        FROM device_latest_telemetry
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    conn.close()

    if not row:
        return {
            "device_id": device_id,
            "telemetry": {},
            "alarm_active": 0,
            "alarm_message": "No telemetry received yet",
            "updated_at": None
        }

    item = dict(row)

    try:
        telemetry = json.loads(item["telemetry"]) if item["telemetry"] else {}
    except Exception:
        telemetry = {}

    return {
        "device_id": device_id,
        "telemetry": telemetry,
        "alarm_active": item["alarm_active"],
        "alarm_message": item["alarm_message"],
        "updated_at": item["updated_at"]
    }

@router.get("/audit-log")
def get_audit_log(
    limit: int = 100,
    action: str = None,
    target_type: str = None,
    target_id: str = None,
    actor: str = None,
    client_id: int = None,
    site_id: int = None,
    building_id: int = None,
    floor_id: int = None,
    room_id: int = None,
    device_id: str = None,
    gateway_id: str = None,
    user_id: int = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None
):
    conn = db()

    where_clauses = []
    params = []

    def add_filter(column_name, value):
        if value is not None and value != "":
            where_clauses.append(f"{column_name} = ?")
            params.append(value)

    add_filter("action", action)
    add_filter("target_type", target_type)
    add_filter("target_id", target_id)
    add_filter("actor", actor)
    add_filter("client_id", client_id)
    add_filter("site_id", site_id)
    add_filter("building_id", building_id)
    add_filter("floor_id", floor_id)
    add_filter("room_id", room_id)
    add_filter("device_id", device_id)
    add_filter("gateway_id", gateway_id)
    add_filter("user_id", user_id)

    if search:
        where_clauses.append("""
            (
                action LIKE ?
                OR target_type LIKE ?
                OR target_id LIKE ?
                OR actor LIKE ?
                OR message LIKE ?
                OR details LIKE ?
            )
        """)
        search_value = f"%{search}%"
        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if from_date:
        where_clauses.append("created_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("created_at <= ?")

        if len(to_date) == 10:
            params.append(to_date + " 23:59:59")
        else:
            params.append(to_date)

    where_sql = ""

    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    if limit < 1:
        limit = 100

    if limit > 500:
        limit = 500

    rows = conn.execute(f"""
        SELECT *
        FROM audit_log
        {where_sql}
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    conn.close()

    result = []

    for row in rows:
        item = dict(row)

        try:
            item["details"] = json.loads(item["details"]) if item["details"] else {}
        except Exception:
            item["details"] = {}

        if not item.get("message"):
            item["message"] = build_audit_message(
                action=item.get("action"),
                actor=item.get("actor"),
                target_type=item.get("target_type"),
                target_id=item.get("target_id"),
                details=item.get("details")
            )

        item["timestamp"] = item.get("created_at")

        result.append(item)

    return result

@router.get("/audit-log/export.csv")
def export_audit_log_csv(
    limit: int = 1000,
    action: str = None,
    target_type: str = None,
    target_id: str = None,
    actor: str = None,
    client_id: int = None,
    site_id: int = None,
    building_id: int = None,
    floor_id: int = None,
    room_id: int = None,
    device_id: str = None,
    gateway_id: str = None,
    user_id: int = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None
):
    conn = db()

    where_clauses = []
    params = []

    def add_filter(column_name, value):
        if value is not None and value != "":
            where_clauses.append(f"{column_name} = ?")
            params.append(value)

    add_filter("action", action)
    add_filter("target_type", target_type)
    add_filter("target_id", target_id)
    add_filter("actor", actor)
    add_filter("client_id", client_id)
    add_filter("site_id", site_id)
    add_filter("building_id", building_id)
    add_filter("floor_id", floor_id)
    add_filter("room_id", room_id)
    add_filter("device_id", device_id)
    add_filter("gateway_id", gateway_id)
    add_filter("user_id", user_id)

    if search:
        where_clauses.append("""
            (
                action LIKE ?
                OR target_type LIKE ?
                OR target_id LIKE ?
                OR actor LIKE ?
                OR message LIKE ?
                OR details LIKE ?
            )
        """)

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if from_date:
        where_clauses.append("created_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("created_at <= ?")

        if len(to_date) == 10:
            params.append(to_date + " 23:59:59")
        else:
            params.append(to_date)

    where_sql = ""

    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    if limit < 1:
        limit = 1000

    if limit > 5000:
        limit = 5000

    rows = conn.execute(f"""
        SELECT *
        FROM audit_log
        {where_sql}
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    output = io.StringIO()

    fieldnames = [
        "id",
        "timestamp",
        "actor",
        "action",
        "target_type",
        "target_id",
        "message",
        "client_id",
        "site_id",
        "building_id",
        "floor_id",
        "room_id",
        "device_id",
        "gateway_id",
        "user_id",
        "details"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        item = dict(row)

        try:
            details_obj = json.loads(item["details"]) if item.get("details") else {}
            details_text = json.dumps(details_obj, ensure_ascii=False)
        except Exception:
            details_text = item.get("details") or ""

        message = item.get("message")

        if not message:
            try:
                details_for_message = json.loads(item["details"]) if item.get("details") else {}
            except Exception:
                details_for_message = {}

            message = build_audit_message(
                action=item.get("action"),
                actor=item.get("actor"),
                target_type=item.get("target_type"),
                target_id=item.get("target_id"),
                details=details_for_message
            )

        writer.writerow({
            "id": item.get("id"),
            "timestamp": item.get("created_at"),
            "actor": item.get("actor"),
            "action": item.get("action"),
            "target_type": item.get("target_type"),
            "target_id": item.get("target_id"),
            "message": message,
            "client_id": item.get("client_id"),
            "site_id": item.get("site_id"),
            "building_id": item.get("building_id"),
            "floor_id": item.get("floor_id"),
            "room_id": item.get("room_id"),
            "device_id": item.get("device_id"),
            "gateway_id": item.get("gateway_id"),
            "user_id": item.get("user_id"),
            "details": details_text
        })

    conn.close()

    output.seek(0)

    export_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"audit_log_export_{export_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/admin/export/device-inventory.csv")
def admin_device_inventory_export_csv():
    conn = db()

    def rows_to_dicts(query, params=()):
        try:
            return [dict(row) for row in conn.execute(query, params).fetchall()]
        except Exception as e:
            print("CSV query error:", e)
            return []

    def get_name(row, keys=("name", "label", "title", "room_name")):
        if not row:
            return ""

        for key in keys:
            value = row.get(key)
            if value:
                return value

        return ""

    def safe_details(data):
        safe_data = dict(data or {})

        secret_keys = [
            "app_key",
            "api_key",
            "password",
            "token",
            "secret"
        ]

        for key in list(safe_data.keys()):
            if key.lower() in secret_keys:
                safe_data[key] = "***hidden***"

        try:
            return json.dumps(safe_data, ensure_ascii=False, default=str)
        except Exception:
            return str(safe_data)

    def parse_json_maybe(value):
        if value is None:
            return {}

        if isinstance(value, dict):
            return value

        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {}

        return {}

    def has_value(value):
        return value is not None and value != "" and value != "null"

    def merge_telemetry(target, source):
        source = source or {}

        for key, value in source.items():
            if has_value(value):
                target[key] = value

        return target

    def tb_has_real_values(tb_telemetry):
        if not tb_telemetry:
            return False

        if tb_telemetry.get("last_seen_ts") is not None:
            return True

        useful_keys = [
            "temperature",
            "humidity",
            "motion",
            "alarm",
            "voltage",
            "current",
            "power"
        ]

        for key in useful_keys:
            if tb_telemetry.get(key) is not None:
                return True

        return False

    clients = rows_to_dicts("SELECT * FROM clients ORDER BY id")
    sites = rows_to_dicts("SELECT * FROM sites ORDER BY id")
    buildings = rows_to_dicts("SELECT * FROM buildings ORDER BY id")
    floors = rows_to_dicts("SELECT * FROM floors ORDER BY id")
    rooms = rows_to_dicts("SELECT * FROM rooms ORDER BY id")
    devices = rows_to_dicts("SELECT * FROM devices ORDER BY device_id")

    clients_by_id = {row.get("id"): row for row in clients}
    sites_by_id = {row.get("id"): row for row in sites}
    buildings_by_id = {row.get("id"): row for row in buildings}
    floors_by_id = {row.get("id"): row for row in floors}
    rooms_by_id = {row.get("id"): row for row in rooms}

    capability_rows = rows_to_dicts("""
        SELECT device_id, capability
        FROM device_capabilities
        ORDER BY device_id, capability
    """)

    capabilities_by_device = {}

    for row in capability_rows:
        capability_device_id = row.get("device_id")

        if capability_device_id not in capabilities_by_device:
            capabilities_by_device[capability_device_id] = []

        capabilities_by_device[capability_device_id].append(row.get("capability"))

    alarm_rows = rows_to_dicts("""
        SELECT *
        FROM alarm_history
        ORDER BY datetime(triggered_at) DESC, id DESC
    """)

    latest_alarm_by_device = {}
    active_alarm_by_device = {}

    for alarm in alarm_rows:
        alarm_device_id = alarm.get("device_id")

        if not alarm_device_id:
            continue

        if alarm_device_id not in latest_alarm_by_device:
            latest_alarm_by_device[alarm_device_id] = alarm

        if alarm.get("resolved") in [0, "0", False, None]:
            if alarm_device_id not in active_alarm_by_device:
                active_alarm_by_device[alarm_device_id] = alarm

    def resolve_device_location(device):
        room = None
        floor = None
        building = None
        site = None
        client = None

        room_id = device.get("room_id")
        floor_id = device.get("floor_id")
        building_id = device.get("building_id")
        site_id = device.get("site_id")
        client_id = device.get("client_id")

        if room_id:
            room = rooms_by_id.get(room_id)

        if room:
            room_floor_id = room.get("floor_id")
            if room_floor_id:
                floor = floors_by_id.get(room_floor_id)

        if not floor and floor_id:
            floor = floors_by_id.get(floor_id)

        if floor:
            floor_building_id = floor.get("building_id")
            if floor_building_id:
                building = buildings_by_id.get(floor_building_id)

        if not building and building_id:
            building = buildings_by_id.get(building_id)

        if building:
            building_site_id = building.get("site_id")
            if building_site_id:
                site = sites_by_id.get(building_site_id)

        if not site and site_id:
            site = sites_by_id.get(site_id)

        if site:
            site_client_id = site.get("client_id")
            if site_client_id:
                client = clients_by_id.get(site_client_id)

        if not client and client_id:
            client = clients_by_id.get(client_id)

        return client, site, building, floor, room

    def get_inventory_telemetry(device_id):
        telemetry = {}
        sources = []

        latest_alarm = latest_alarm_by_device.get(device_id)

        if latest_alarm and latest_alarm.get("telemetry"):
            alarm_telemetry = parse_json_maybe(latest_alarm.get("telemetry"))
            telemetry = merge_telemetry(telemetry, alarm_telemetry)
            sources.append("alarm_history")

        try:
            tb_telemetry = read_tb_latest_telemetry(device_id) or {}
        except Exception as e:
            print("TB telemetry failed during CSV export:", e)
            tb_telemetry = {}

        if tb_has_real_values(tb_telemetry):
            telemetry = merge_telemetry(telemetry, tb_telemetry)
            sources.append("thingsboard")

        try:
            local_telemetry = get_local_latest_telemetry(conn, device_id) or {}
        except Exception as e:
            print("Local telemetry failed during CSV export:", e)
            local_telemetry = {}

        if local_telemetry:
            telemetry = merge_telemetry(telemetry, local_telemetry)
            sources.append("local_latest")

        active_alarm = active_alarm_by_device.get(device_id)

        if active_alarm:
            telemetry["alarm_active"] = True
            telemetry["alarm_message"] = active_alarm.get("alarm_message", "Active alarm")
        else:
            if "alarm_active" not in telemetry:
                telemetry["alarm_active"] = False

            if not telemetry.get("alarm_message"):
                telemetry["alarm_message"] = "OK"

        if not telemetry.get("latest_telemetry_source"):
            if sources:
                telemetry["latest_telemetry_source"] = ", ".join(sources)
            else:
                telemetry["latest_telemetry_source"] = "none"

        return telemetry

    output = io.StringIO()

    fieldnames = [
        "client_id",
        "client_name",
        "site_id",
        "site_name",
        "building_id",
        "building_name",
        "floor_id",
        "floor_name",
        "floor_number",
        "room_id",
        "room_name",

        "device_id",
        "chip_mac",
        "dev_eui",
        "join_eui",
        "node_type",
        "label",
        "icon_type",
        "capabilities",

        "x",
        "y",

        "device_status",
        "last_seen_iso",
        "last_seen_seconds_ago",
        "local_updated_at",

        "battery_percent",
        "battery_voltage",
        "power_source",
        "battery_status",

        "signal_status",
        "gateway_id",
        "received_by_gateways",
        "rssi",
        "snr",
        "spreading_factor",
        "bandwidth",
        "frequency",

        "alarm_active",
        "alarm_message",
        "active_alarm_id",
        "active_alarm_type",
        "active_alarm_triggered_at",

        "temperature",
        "humidity",
        "co2",
        "voc",
        "motion",
        "presence",
        "water_leak",
        "gas_alarm",
        "smoke_alarm",
        "power",
        "voltage",
        "current",

        "latest_telemetry_source",
        "telemetry_json",
        "details"
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for device in devices:
        device_id = device.get("device_id")

        client, site, building, floor, room = resolve_device_location(device)

        telemetry = get_inventory_telemetry(device_id)

        latest_alarm = latest_alarm_by_device.get(device_id)
        active_alarm = active_alarm_by_device.get(device_id)

        capabilities = capabilities_by_device.get(device_id, [])

        if not capabilities:
            node_type = device.get("node_type", "")

            if node_type == "multi":
                capabilities = [
                    "environment",
                    "energy",
                    "safety",
                    "occupancy"
                ]
            elif node_type:
                capabilities = [node_type]

        last_seen_value = (
            telemetry.get("last_seen_iso")
            or telemetry.get("local_updated_at")
            or device.get("last_seen", "")
        )

        device_status = (
            telemetry.get("device_status")
            or device.get("status", "")
        )

        if not device_status and telemetry.get("local_updated_at"):
            device_status = "telemetry_received"

        writer.writerow({
            "client_id": client.get("id") if client else "",
            "client_name": get_name(client),

            "site_id": site.get("id") if site else "",
            "site_name": get_name(site),

            "building_id": building.get("id") if building else "",
            "building_name": get_name(building) or device.get("building", ""),

            "floor_id": floor.get("id") if floor else "",
            "floor_name": get_name(floor) or device.get("floor", ""),
            "floor_number": floor.get("floor_number") if floor else device.get("floor", ""),

            "room_id": room.get("id") if room else device.get("room_id", ""),
            "room_name": get_name(room) or device.get("room", ""),

            "device_id": device_id,
            "chip_mac": device.get("chip_mac", ""),
            "dev_eui": device.get("dev_eui", ""),
            "join_eui": device.get("join_eui", ""),
            "node_type": device.get("node_type", ""),
            "label": device.get("label", ""),
            "icon_type": device.get("icon_type", ""),
            "capabilities": ", ".join([str(item) for item in capabilities]),

            "x": device.get("x", ""),
            "y": device.get("y", ""),

            "device_status": device_status,
            "last_seen_iso": last_seen_value,
            "last_seen_seconds_ago": telemetry.get("last_seen_seconds_ago", ""),
            "local_updated_at": telemetry.get("local_updated_at", ""),

            "battery_percent": telemetry.get("battery_percent", telemetry.get("battery", "")),
            "battery_voltage": telemetry.get("battery_voltage", ""),
            "power_source": telemetry.get("power_source", ""),
            "battery_status": telemetry.get("battery_status", ""),

            "signal_status": telemetry.get("signal_status", ""),
            "gateway_id": telemetry.get("gateway_id", ""),
            "received_by_gateways": telemetry.get("received_by_gateways", ""),
            "rssi": telemetry.get("rssi", ""),
            "snr": telemetry.get("snr", ""),
            "spreading_factor": telemetry.get("spreading_factor", ""),
            "bandwidth": telemetry.get("bandwidth", ""),
            "frequency": telemetry.get("frequency", ""),

            "alarm_active": telemetry.get("alarm_active", True if active_alarm else False),
            "alarm_message": telemetry.get(
                "alarm_message",
                active_alarm.get("alarm_message") if active_alarm else "OK"
            ),
            "active_alarm_id": active_alarm.get("id") if active_alarm else "",
            "active_alarm_type": active_alarm.get("alarm_type") if active_alarm else "",
            "active_alarm_triggered_at": active_alarm.get("triggered_at") if active_alarm else "",

            "temperature": telemetry.get("temperature", ""),
            "humidity": telemetry.get("humidity", ""),
            "co2": telemetry.get("co2", ""),
            "voc": telemetry.get("voc", ""),
            "motion": telemetry.get("motion", ""),
            "presence": telemetry.get("presence", ""),
            "water_leak": telemetry.get("water_leak", ""),
            "gas_alarm": telemetry.get("gas_alarm", ""),
            "smoke_alarm": telemetry.get("smoke_alarm", ""),
            "power": telemetry.get("power", ""),
            "voltage": telemetry.get("voltage", ""),
            "current": telemetry.get("current", ""),

            "latest_telemetry_source": telemetry.get("latest_telemetry_source", "none"),
            "telemetry_json": json.dumps(telemetry, ensure_ascii=False, default=str),
            "details": safe_details(device)
        })

    conn.close()

    output.seek(0)

    export_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"admin_device_inventory_export_{export_date}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/client-portal/{user_id}/activity-log")
def client_portal_activity_log(
    user_id: int,
    limit: int = 100,
    action: str = None,
    target_type: str = None,
    device_id: str = None,
    gateway_id: str = None,
    floor_id: int = None,
    building_id: int = None,
    search: str = None,
    from_date: str = None,
    to_date: str = None
):
    conn = db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if user["enabled"] != 1:
        conn.close()
        raise HTTPException(status_code=403, detail="User is disabled")

    access_rows = conn.execute("""
        SELECT *
        FROM user_access
        WHERE user_id = ?
    """, (user_id,)).fetchall()

    if not access_rows:
        conn.close()
        return []

    allowed_actions = set()

    for access in access_rows:
        if access["can_view_alarms"]:
            allowed_actions.add("acknowledge_alarm")
            allowed_actions.add("resolve_alarm")

        if access["can_view_devices"]:
            allowed_actions.add("move_device")

        if access["can_view_gateways"]:
            allowed_actions.add("move_gateway")
            allowed_actions.add("update_gateway")
            allowed_actions.add("create_gateway")

    if not allowed_actions:
        conn.close()
        return []

    where_clauses = []
    params = []

    action_placeholders = ",".join(["?"] * len(allowed_actions))

    where_clauses.append(f"""
        action IN ({action_placeholders})
    """)

    params.extend(list(allowed_actions))

    scope_clauses = []
    scope_params = []

    for access in access_rows:
        access_client_id = access["client_id"]
        access_site_id = access["site_id"]
        access_building_id = access["building_id"]
        access_floor_id = access["floor_id"]

        if access_floor_id:
            scope_clauses.append("""
                floor_id = ?
            """)
            scope_params.append(access_floor_id)

        elif access_building_id:
            scope_clauses.append("""
                (
                    building_id = ?
                    OR floor_id IN (
                        SELECT id
                        FROM floors
                        WHERE building_id = ?
                    )
                )
            """)
            scope_params.extend([
                access_building_id,
                access_building_id
            ])

        elif access_site_id:
            scope_clauses.append("""
                (
                    site_id = ?
                    OR building_id IN (
                        SELECT id
                        FROM buildings
                        WHERE site_id = ?
                    )
                    OR floor_id IN (
                        SELECT f.id
                        FROM floors f
                        JOIN buildings b ON f.building_id = b.id
                        WHERE b.site_id = ?
                    )
                )
            """)
            scope_params.extend([
                access_site_id,
                access_site_id,
                access_site_id
            ])

        elif access_client_id:
            scope_clauses.append("""
                (
                    client_id = ?
                    OR site_id IN (
                        SELECT id
                        FROM sites
                        WHERE client_id = ?
                    )
                    OR building_id IN (
                        SELECT b.id
                        FROM buildings b
                        JOIN sites s ON b.site_id = s.id
                        WHERE s.client_id = ?
                    )
                    OR floor_id IN (
                        SELECT f.id
                        FROM floors f
                        JOIN buildings b ON f.building_id = b.id
                        JOIN sites s ON b.site_id = s.id
                        WHERE s.client_id = ?
                    )
                )
            """)
            scope_params.extend([
                access_client_id,
                access_client_id,
                access_client_id,
                access_client_id
            ])

    if not scope_clauses:
        conn.close()
        return []

    where_clauses.append("(" + " OR ".join(scope_clauses) + ")")
    params.extend(scope_params)

    def add_filter(column_name, value):
        if value is not None and value != "":
            where_clauses.append(f"{column_name} = ?")
            params.append(value)

    add_filter("action", action)
    add_filter("target_type", target_type)
    add_filter("device_id", device_id)
    add_filter("gateway_id", gateway_id)
    add_filter("floor_id", floor_id)
    add_filter("building_id", building_id)

    if search:
        where_clauses.append("""
            (
                action LIKE ?
                OR target_type LIKE ?
                OR target_id LIKE ?
                OR message LIKE ?
                OR details LIKE ?
            )
        """)

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if from_date:
        where_clauses.append("created_at >= ?")
        params.append(from_date)

    if to_date:
        where_clauses.append("created_at <= ?")

        if len(to_date) == 10:
            params.append(to_date + " 23:59:59")
        else:
            params.append(to_date)

    if limit < 1:
        limit = 100

    if limit > 300:
        limit = 300

    where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = conn.execute(f"""
        SELECT *
        FROM audit_log
        {where_sql}
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
    """, params + [limit]).fetchall()

    conn.close()

    result = []

    for row in rows:
        item = dict(row)

        try:
            item["details"] = json.loads(item["details"]) if item["details"] else {}
        except Exception:
            item["details"] = {}

        if not item.get("message"):
            item["message"] = build_audit_message(
                action=item.get("action"),
                actor=item.get("actor"),
                target_type=item.get("target_type"),
                target_id=item.get("target_id"),
                details=item.get("details")
            )

        item["timestamp"] = item.get("created_at")

        result.append(item)

    return result

@router.delete("/clients/{client_id}")
def delete_client(client_id: int):
    conn = db()

    client = conn.execute("""
        SELECT *
        FROM clients
        WHERE id = ?
    """, (client_id,)).fetchone()

    if not client:
        conn.close()
        raise HTTPException(status_code=404, detail="Client not found")

    site_ids = get_ids(conn, """
        SELECT id
        FROM sites
        WHERE client_id = ?
    """, (client_id,))

    building_ids = []

    if site_ids:
        placeholders = ",".join("?" for _ in site_ids)
        building_ids = get_ids(conn, f"""
            SELECT id
            FROM buildings
            WHERE site_id IN ({placeholders})
        """, site_ids)

    floor_ids = []

    if building_ids:
        placeholders = ",".join("?" for _ in building_ids)
        floor_ids = get_ids(conn, f"""
            SELECT id
            FROM floors
            WHERE building_id IN ({placeholders})
        """, building_ids)

    room_ids = get_room_ids_for_floors(conn, floor_ids)
    floorplan_ids = get_floorplan_ids_for_floors_and_rooms(conn, floor_ids, room_ids)

    devices_count = conn.execute("""
        SELECT COUNT(*)
        FROM devices
        WHERE client_id = ?
    """, (client_id,)).fetchone()[0]

    conn.execute("""
        UPDATE devices
        SET client_id = NULL,
            site_id = NULL,
            building_id = NULL,
            floor_id = NULL,
            room_id = NULL,
            building = NULL,
            floor = NULL,
            room = NULL,
            x = NULL,
            y = NULL
        WHERE client_id = ?
    """, (client_id,))

    gateways_unassigned = safe_unassign_gateways(
        conn,
        client_ids=[client_id],
        site_ids=site_ids,
        building_ids=building_ids,
        floor_ids=floor_ids,
        clear_client=True,
        clear_site=True,
        clear_building=True,
        clear_floor=True
    )

    deleted_user_access = conn.execute("""
        DELETE FROM user_access
        WHERE client_id = ?
    """, (client_id,)).rowcount

    if site_ids:
        placeholders = ",".join("?" for _ in site_ids)
        deleted_user_access += conn.execute(f"""
            DELETE FROM user_access
            WHERE site_id IN ({placeholders})
        """, site_ids).rowcount

        deleted_site_maps = conn.execute(f"""
            DELETE FROM site_maps
            WHERE site_id IN ({placeholders})
        """, site_ids).rowcount
    else:
        deleted_site_maps = 0

    if building_ids:
        placeholders = ",".join("?" for _ in building_ids)
        deleted_user_access += conn.execute(f"""
            DELETE FROM user_access
            WHERE building_id IN ({placeholders})
        """, building_ids).rowcount

    if floor_ids:
        placeholders = ",".join("?" for _ in floor_ids)
        deleted_user_access += conn.execute(f"""
            DELETE FROM user_access
            WHERE floor_id IN ({placeholders})
        """, floor_ids).rowcount

    deleted_rooms = delete_by_ids(conn, "rooms", room_ids)
    deleted_floorplans = delete_by_ids(conn, "floorplans", floorplan_ids)
    deleted_floors = delete_by_ids(conn, "floors", floor_ids)
    deleted_buildings = delete_by_ids(conn, "buildings", building_ids)
    deleted_sites = delete_by_ids(conn, "sites", site_ids)

    conn.execute("""
        DELETE FROM clients
        WHERE id = ?
    """, (client_id,))

    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "client_id": client_id,
        "deleted": {
            "sites": deleted_sites,
            "buildings": deleted_buildings,
            "floors": deleted_floors,
            "rooms": deleted_rooms,
            "floorplans": deleted_floorplans,
            "site_maps": deleted_site_maps,
            "user_access_records": deleted_user_access
        },
        "devices_preserved_and_unassigned": devices_count,
        "gateways_preserved_and_unassigned": gateways_unassigned
    }

@router.delete("/sites/{site_id}")
def delete_site(site_id: int):
    conn = db()

    site = conn.execute("""
        SELECT *
        FROM sites
        WHERE id = ?
    """, (site_id,)).fetchone()

    if not site:
        conn.close()
        raise HTTPException(status_code=404, detail="Site not found")

    building_ids = get_ids(conn, """
        SELECT id
        FROM buildings
        WHERE site_id = ?
    """, (site_id,))

    floor_ids = []

    if building_ids:
        placeholders = ",".join("?" for _ in building_ids)
        floor_ids = get_ids(conn, f"""
            SELECT id
            FROM floors
            WHERE building_id IN ({placeholders})
        """, building_ids)

    room_ids = get_room_ids_for_floors(conn, floor_ids)
    floorplan_ids = get_floorplan_ids_for_floors_and_rooms(conn, floor_ids, room_ids)

    devices_count = conn.execute("""
        SELECT COUNT(*)
        FROM devices
        WHERE site_id = ?
    """, (site_id,)).fetchone()[0]

    conn.execute("""
        UPDATE devices
        SET site_id = NULL,
            building_id = NULL,
            floor_id = NULL,
            room_id = NULL,
            building = NULL,
            floor = NULL,
            room = NULL,
            x = NULL,
            y = NULL
        WHERE site_id = ?
    """, (site_id,))

    gateways_unassigned = safe_unassign_gateways(
        conn,
        site_ids=[site_id],
        building_ids=building_ids,
        floor_ids=floor_ids,
        clear_site=True,
        clear_building=True,
        clear_floor=True
    )

    deleted_user_access = conn.execute("""
        DELETE FROM user_access
        WHERE site_id = ?
    """, (site_id,)).rowcount

    if building_ids:
        placeholders = ",".join("?" for _ in building_ids)
        deleted_user_access += conn.execute(f"""
            DELETE FROM user_access
            WHERE building_id IN ({placeholders})
        """, building_ids).rowcount

    if floor_ids:
        placeholders = ",".join("?" for _ in floor_ids)
        deleted_user_access += conn.execute(f"""
            DELETE FROM user_access
            WHERE floor_id IN ({placeholders})
        """, floor_ids).rowcount

    deleted_site_maps = conn.execute("""
        DELETE FROM site_maps
        WHERE site_id = ?
    """, (site_id,)).rowcount

    deleted_rooms = delete_by_ids(conn, "rooms", room_ids)
    deleted_floorplans = delete_by_ids(conn, "floorplans", floorplan_ids)
    deleted_floors = delete_by_ids(conn, "floors", floor_ids)
    deleted_buildings = delete_by_ids(conn, "buildings", building_ids)

    conn.execute("""
        DELETE FROM sites
        WHERE id = ?
    """, (site_id,))

    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "site_id": site_id,
        "deleted": {
            "buildings": deleted_buildings,
            "floors": deleted_floors,
            "rooms": deleted_rooms,
            "floorplans": deleted_floorplans,
            "site_maps": deleted_site_maps,
            "user_access_records": deleted_user_access
        },
        "devices_preserved_and_unassigned": devices_count,
        "gateways_preserved_and_unassigned": gateways_unassigned
    }

@router.delete("/buildings/{building_id}")
def delete_building(building_id: int):
    conn = db()

    building = conn.execute("""
        SELECT *
        FROM buildings
        WHERE id = ?
    """, (building_id,)).fetchone()

    if not building:
        conn.close()
        raise HTTPException(status_code=404, detail="Building not found")

    floor_ids = get_ids(conn, """
        SELECT id
        FROM floors
        WHERE building_id = ?
    """, (building_id,))

    room_ids = get_room_ids_for_floors(conn, floor_ids)
    floorplan_ids = get_floorplan_ids_for_floors_and_rooms(conn, floor_ids, room_ids)

    devices_count = conn.execute("""
        SELECT COUNT(*)
        FROM devices
        WHERE building_id = ?
    """, (building_id,)).fetchone()[0]

    conn.execute("""
        UPDATE devices
        SET building_id = NULL,
            floor_id = NULL,
            room_id = NULL,
            building = NULL,
            floor = NULL,
            room = NULL,
            x = NULL,
            y = NULL
        WHERE building_id = ?
    """, (building_id,))

    gateways_unassigned = safe_unassign_gateways(
        conn,
        building_ids=[building_id],
        floor_ids=floor_ids,
        clear_building=True,
        clear_floor=True
    )

    deleted_user_access = conn.execute("""
        DELETE FROM user_access
        WHERE building_id = ?
    """, (building_id,)).rowcount

    if floor_ids:
        placeholders = ",".join("?" for _ in floor_ids)
        deleted_user_access += conn.execute(f"""
            DELETE FROM user_access
            WHERE floor_id IN ({placeholders})
        """, floor_ids).rowcount

    deleted_rooms = delete_by_ids(conn, "rooms", room_ids)
    deleted_floorplans = delete_by_ids(conn, "floorplans", floorplan_ids)
    deleted_floors = delete_by_ids(conn, "floors", floor_ids)

    conn.execute("""
        DELETE FROM buildings
        WHERE id = ?
    """, (building_id,))

    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "building_id": building_id,
        "deleted": {
            "floors": deleted_floors,
            "rooms": deleted_rooms,
            "floorplans": deleted_floorplans,
            "user_access_records": deleted_user_access
        },
        "devices_preserved_and_unassigned": devices_count,
        "gateways_preserved_and_unassigned": gateways_unassigned
    }

@router.delete("/floors/{floor_id}")
def delete_floor(floor_id: int):
    conn = db()

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (floor_id,)).fetchone()

    if not floor:
        conn.close()
        raise HTTPException(status_code=404, detail="Floor not found")

    room_rows = conn.execute("""
        SELECT *
        FROM rooms
        WHERE floor_id = ?
           OR floorplan_id = ?
    """, (floor_id, floor_id)).fetchall()

    room_ids = [row["id"] for row in room_rows]
    floorplan_ids = get_floorplan_ids_for_floors_and_rooms(conn, [floor_id], room_ids)

    devices_count = conn.execute("""
        SELECT COUNT(*)
        FROM devices
        WHERE floor_id = ?
           OR room_id IN (
                SELECT id
                FROM rooms
                WHERE floor_id = ?
                   OR floorplan_id = ?
           )
    """, (floor_id, floor_id, floor_id)).fetchone()[0]

    conn.execute("""
        UPDATE devices
        SET floor_id = NULL,
            room_id = NULL,
            floor = NULL,
            room = NULL,
            x = NULL,
            y = NULL
        WHERE floor_id = ?
           OR room_id IN (
                SELECT id
                FROM rooms
                WHERE floor_id = ?
                   OR floorplan_id = ?
           )
    """, (floor_id, floor_id, floor_id))

    gateways_unassigned = safe_unassign_gateways(
        conn,
        floor_ids=[floor_id],
        clear_floor=True
    )

    deleted_user_access = conn.execute("""
        DELETE FROM user_access
        WHERE floor_id = ?
    """, (floor_id,)).rowcount

    deleted_rooms = delete_by_ids(conn, "rooms", room_ids)
    deleted_floorplans = delete_by_ids(conn, "floorplans", floorplan_ids)

    conn.execute("""
        DELETE FROM floors
        WHERE id = ?
    """, (floor_id,))

    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "floor_id": floor_id,
        "deleted": {
            "rooms": deleted_rooms,
            "floorplans": deleted_floorplans,
            "user_access_records": deleted_user_access
        },
        "devices_preserved_and_unassigned": devices_count,
        "gateways_preserved_and_unassigned": gateways_unassigned
    }

@router.put("/clients/{client_id}")
def update_client(client_id: int, data: dict):
    name = data.get("name", "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Client name required")

    conn = db()

    cur = conn.execute("""
        UPDATE clients
        SET name = ?
        WHERE id = ?
    """, (name, client_id))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "status": "updated",
        "client_id": client_id,
        "name": name,
    }

@router.put("/sites/{site_id}")
def update_site(site_id: int, data: dict):
    name = data.get("name", "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Site name required")

    conn = db()

    cur = conn.execute("""
        UPDATE sites
        SET name = ?
        WHERE id = ?
    """, (name, site_id))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Site not found")

    return {
        "status": "updated",
        "site_id": site_id,
        "name": name,
    }

@router.put("/buildings/{building_id}")
def update_building(building_id: int, data: dict):
    name = data.get("name", "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Building name required")

    conn = db()

    cur = conn.execute("""
        UPDATE buildings
        SET name = ?
        WHERE id = ?
    """, (name, building_id))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Building not found")

    return {
        "status": "updated",
        "building_id": building_id,
        "name": name,
    }

@router.put("/floors/{floor_id}")
def update_floor(floor_id: int, data: dict):
    name = data.get("name", "").strip()
    floor_number = data.get("floor_number")

    if not name:
        raise HTTPException(status_code=400, detail="Floor name required")

    conn = db()

    cur = conn.execute("""
        UPDATE floors
        SET name = ?,
            floor_number = ?
        WHERE id = ?
    """, (name, floor_number, floor_id))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Floor not found")

    return {
        "status": "updated",
        "floor_id": floor_id,
        "name": name,
        "floor_number": floor_number,
    }

@router.post("/floors/{floor_id}/rooms")
def create_room_for_floor(floor_id: int, data: dict):
    room_name = data.get("room_name", "").strip()
    polygon_points = data.get("polygon_points", [])

    if not room_name:
        raise HTTPException(status_code=400, detail="room_name required")

    if not isinstance(polygon_points, list) or len(polygon_points) < 3:
        raise HTTPException(status_code=400, detail="polygon_points must contain at least 3 points")

    conn = db()

    floor = conn.execute("""
        SELECT f.*, b.name AS building_name
        FROM floors f
        JOIN buildings b ON f.building_id = b.id
        WHERE f.id = ?
    """, (floor_id,)).fetchone()

    if not floor:
        conn.close()
        raise HTTPException(status_code=404, detail="Floor not found")

    x_values = [p["x"] for p in polygon_points]
    y_values = [p["y"] for p in polygon_points]

    center_x = int(sum(x_values) / len(x_values))
    center_y = int(sum(y_values) / len(y_values))

    cur = conn.execute("""
        INSERT INTO rooms (
            floorplan_id,
            floor_id,
            building,
            floor,
            room_name,
            polygon_points,
            x,
            y
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        0,
        floor_id,
        floor["building_name"],
        floor["name"],
        room_name,
        json.dumps(polygon_points),
        center_x,
        center_y,
    ))

    conn.commit()
    room_id = cur.lastrowid
    conn.close()

    return {
        "status": "created",
        "room_id": room_id,
        "floor_id": floor_id,
        "room_name": room_name,
        "x": center_x,
        "y": center_y,
        "polygon_points": polygon_points,
    }

@router.get("/rooms/{room_id}")
def get_room(room_id: int):
    conn = db()

    room = conn.execute("""
        SELECT *
        FROM rooms
        WHERE id = ?
    """, (room_id,)).fetchone()

    conn.close()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    result = dict(room)

    if result.get("polygon_points"):
        result["polygon_points"] = json.loads(result["polygon_points"])

    return result

@router.post("/rooms/{room_id}/devices")
def assign_device_to_room(room_id: int, data: dict):

    device_id = data.get("device_id")

    if not device_id:
        raise HTTPException(
            status_code=400,
            detail="device_id required"
        )

    conn = db()

    room = conn.execute("""
        SELECT
            r.id as room_id,
            r.floor_id,
            f.building_id
        FROM rooms r
        JOIN floors f
            ON r.floor_id = f.id
        WHERE r.id = ?
    """, (room_id,)).fetchone()

    if not room:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    building = conn.execute("""
        SELECT
            b.id as building_id,
            b.site_id
        FROM buildings b
        WHERE b.id = ?
    """, (room["building_id"],)).fetchone()

    site = conn.execute("""
        SELECT
            s.id as site_id,
            s.client_id
        FROM sites s
        WHERE s.id = ?
    """, (building["site_id"],)).fetchone()

    cur = conn.execute("""
        UPDATE devices
        SET
            client_id = ?,
            site_id = ?,
            building_id = ?,
            floor_id = ?,
            room_id = ?
        WHERE device_id = ?
    """, (
        site["client_id"],
        building["site_id"],
        room["building_id"],
        room["floor_id"],
        room_id,
        device_id
    ))

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    conn.close()

    return {
        "status": "assigned",
        "device_id": device_id,
        "client_id": site["client_id"],
        "site_id": building["site_id"],
        "building_id": room["building_id"],
        "floor_id": room["floor_id"],
        "room_id": room_id
    }

@router.get("/hierarchy")
def get_hierarchy():

    conn = db()

    clients = conn.execute("""
        SELECT *
        FROM clients
        ORDER BY name
    """).fetchall()

    result = []

    for client in clients:

        client_obj = dict(client)
        client_obj["sites"] = []

        sites = conn.execute("""
            SELECT *
            FROM sites
            WHERE client_id = ?
            ORDER BY name
        """, (client["id"],)).fetchall()

        for site in sites:

            site_obj = dict(site)
            site_obj["buildings"] = []

            buildings = conn.execute("""
                SELECT *
                FROM buildings
                WHERE site_id = ?
                ORDER BY name
            """, (site["id"],)).fetchall()

            for building in buildings:

                building_obj = dict(building)
                building_obj["floors"] = []

                floors = conn.execute("""
                    SELECT *
                    FROM floors
                    WHERE building_id = ?
                    ORDER BY floor_number
                """, (building["id"],)).fetchall()

                for floor in floors:

                    floor_obj = dict(floor)
                    floor_obj["rooms"] = []

                    rooms = conn.execute("""
                        SELECT *
                        FROM rooms
                        WHERE floor_id = ?
                        ORDER BY room_name
                    """, (floor["id"],)).fetchall()

                    for room in rooms:

                        room_obj = dict(room)

                        devices = conn.execute("""
                            SELECT
                                device_id,
                                node_type,
                                label,
                                room_id,
                                floor_id,
                                building_id,
                                site_id,
                                client_id
                            FROM devices
                            WHERE room_id = ?
                            ORDER BY label
                        """, (room["id"],)).fetchall()

                        room_obj["devices"] = [
                            dict(d)
                            for d in devices
                        ]

                        floor_obj["rooms"].append(room_obj)

                    building_obj["floors"].append(floor_obj)

                site_obj["buildings"].append(building_obj)

            client_obj["sites"].append(site_obj)

        result.append(client_obj)

    conn.close()

    return result

@router.post("/sites/{site_id}/upload-site-map")
async def upload_site_map(
    site_id: int,
    image: UploadFile = File(...)
):
    conn = db()

    site = conn.execute("""
        SELECT *
        FROM sites
        WHERE id = ?
    """, (site_id,)).fetchone()

    if not site:
        conn.close()
        raise HTTPException(status_code=404, detail="Site not found")

    file_ext = os.path.splitext(image.filename)[1].lower()

    if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Only JPG, PNG, or WEBP images are allowed")

    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", site["name"])

    filename = f"site_{site_id}_{safe_name}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await image.read()

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid image file")

    image_path = f"/uploads/{filename}"

    conn.execute("""
        INSERT INTO site_maps (
            site_id,
            image_path,
            image_width,
            image_height
        ) VALUES (?, ?, ?, ?)
    """, (
        site_id,
        image_path,
        width,
        height,
    ))

    conn.execute("""
        UPDATE sites
        SET campus_image_path = ?,
            image_width = ?,
            image_height = ?
        WHERE id = ?
    """, (
        image_path,
        width,
        height,
        site_id,
    ))

    conn.commit()
    conn.close()

    return {
        "status": "uploaded",
        "site_id": site_id,
        "image_path": image_path,
        "image_width": width,
        "image_height": height,
    }

@router.get("/sites/{site_id}/map")
def get_site_map(site_id: int):

    conn = db()

    site = conn.execute("""
        SELECT *
        FROM sites
        WHERE id = ?
    """, (site_id,)).fetchone()

    if not site:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Site not found"
        )

    buildings = conn.execute("""
        SELECT *
        FROM buildings
        WHERE site_id = ?
        ORDER BY name
    """, (site_id,)).fetchall()

    conn.close()

    result = {
        "site": dict(site),
        "buildings": []
    }

    for b in buildings:

        item = dict(b)

        try:
            item["polygon_points"] = (
                json.loads(item["polygon_points"])
                if item["polygon_points"]
                else []
            )
        except:
            item["polygon_points"] = []

        result["buildings"].append(item)

    return result

@router.put("/buildings/{building_id}/polygon")
def update_building_polygon(
    building_id: int,
    data: dict
):

    polygon_points = data.get("polygon_points", [])

    if len(polygon_points) < 3:
        raise HTTPException(
            status_code=400,
            detail="At least 3 points required"
        )

    x_values = [p["x"] for p in polygon_points]
    y_values = [p["y"] for p in polygon_points]

    center_x = int(sum(x_values) / len(x_values))
    center_y = int(sum(y_values) / len(y_values))

    conn = db()

    cur = conn.execute("""
        UPDATE buildings
        SET
            polygon_points = ?,
            x = ?,
            y = ?
        WHERE id = ?
    """, (
        json.dumps(polygon_points),
        center_x,
        center_y,
        building_id
    ))

    conn.commit()

    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Building not found"
        )

    conn.close()

    return {
        "status": "updated",
        "building_id": building_id,
        "center_x": center_x,
        "center_y": center_y,
        "polygon_points": polygon_points
    }

@router.get("/sites/{site_id}/buildings")
def get_site_buildings(site_id: int):

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM buildings
        WHERE site_id = ?
        ORDER BY name
    """, (site_id,)).fetchall()

    conn.close()

    result = []

    for row in rows:

        item = dict(row)

        try:
            item["polygon_points"] = (
                json.loads(item["polygon_points"])
                if item["polygon_points"]
                else []
            )
        except:
            item["polygon_points"] = []

        result.append(item)

    return result

@router.get("/buildings/{building_id}/floors")
def get_building_floors(building_id: int):

    conn = db()

    rows = conn.execute("""
        SELECT *
        FROM floors
        WHERE building_id = ?
        ORDER BY floor_number
    """, (building_id,)).fetchall()

    conn.close()

    return [dict(r) for r in rows]

@router.get("/floors/{floor_id}/details")
def get_floor_details(floor_id: int):

    conn = db()

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (floor_id,)).fetchone()

    if not floor:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Floor not found"
        )

    rooms = conn.execute("""
        SELECT *
        FROM rooms
        WHERE floor_id = ?
        ORDER BY room_name
    """, (floor_id,)).fetchall()

    result = {
        "floor": dict(floor),
        "rooms": []
    }

    for room in rooms:

        room_obj = dict(room)

        try:
            room_obj["polygon_points"] = (
                json.loads(room_obj["polygon_points"])
                if room_obj["polygon_points"]
                else []
            )
        except:
            room_obj["polygon_points"] = []

        devices = conn.execute("""
            SELECT *
            FROM devices
            WHERE room_id = ?
        """, (room["id"],)).fetchall()

        room_obj["devices"] = [
            dict(d)
            for d in devices
        ]

        result["rooms"].append(room_obj)

    conn.close()

    return result

@router.get("/devices/{device_id}/location")
def get_device_location(device_id: str):

    conn = db()

    device = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    if not device:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    room = conn.execute("""
        SELECT *
        FROM rooms
        WHERE id = ?
    """, (device["room_id"],)).fetchone()

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (device["floor_id"],)).fetchone()

    building = conn.execute("""
        SELECT *
        FROM buildings
        WHERE id = ?
    """, (device["building_id"],)).fetchone()

    site = conn.execute("""
        SELECT *
        FROM sites
        WHERE id = ?
    """, (device["site_id"],)).fetchone()

    client = conn.execute("""
        SELECT *
        FROM clients
        WHERE id = ?
    """, (device["client_id"],)).fetchone()

    conn.close()

    return {
        "device": dict(device),
        "room": dict(room) if room else None,
        "floor": dict(floor) if floor else None,
        "building": dict(building) if building else None,
        "site": dict(site) if site else None,
        "client": dict(client) if client else None
    }

@router.get("/floors/{floor_id}/live")
def get_floor_live(floor_id: int):
    """
    Return one floor with rooms, gateways and profile-driven
    device telemetry for Floor Live View.
    """

    conn = db()

    try:
        # =====================================================
        # 1. LOAD FLOOR
        # =====================================================

        floor = conn.execute(
            """
            SELECT
                f.*,
                b.name AS building_name
            FROM floors AS f
            LEFT JOIN buildings AS b
              ON b.id = f.building_id
            WHERE f.id = ?
            """,
            (floor_id,),
        ).fetchone()

        if not floor:
            raise HTTPException(
                status_code=404,
                detail="Floor not found",
            )

        floor_dict = dict(
            floor
        )

        floor_name = floor_dict.get(
            "name"
        )

        floor_number = floor_dict.get(
            "floor_number"
        )

        building_name = floor_dict.get(
            "building_name"
        )

        # =====================================================
        # 2. LOAD FLOOR ROOMS
        # =====================================================

        rooms = conn.execute(
            """
            SELECT *
            FROM rooms
            WHERE floor_id = ?

               OR floorplan_id IN (
                    SELECT id
                    FROM floorplans
                    WHERE floor_id = ?
               )

               OR (
                    building = ?
                    AND (
                        floor = ?
                        OR floor = ?
                    )
               )

            ORDER BY room_name
            """,
            (
                floor_id,
                floor_id,
                building_name,
                floor_name,
                floor_number,
            ),
        ).fetchall()

        result = {
            "floor": floor_dict,
            "rooms": [],
            "gateways": [],
        }

        # =====================================================
        # 3. BUILD EVERY ROOM
        # =====================================================

        for room in rooms:
            room_obj = dict(
                room
            )

            try:
                room_obj["polygon_points"] = (
                    json.loads(
                        room_obj[
                            "polygon_points"
                        ]
                    )
                    if room_obj.get(
                        "polygon_points"
                    )
                    else []
                )

            except Exception:
                room_obj[
                    "polygon_points"
                ] = []

            devices = conn.execute(
                """
                SELECT DISTINCT *
                FROM devices
                WHERE room_id = ?

                   OR (
                        room = ?

                        AND (
                            floor_id = ?
                            OR floor = ?
                            OR floor = ?
                        )
                   )

                ORDER BY
                    COALESCE(label, device_id),
                    device_id
                """,
                (
                    room["id"],
                    room["room_name"],
                    floor_id,
                    floor_name,
                    floor_number,
                ),
            ).fetchall()

            room_obj["devices"] = []

            # =================================================
            # 4. BUILD EVERY DEVICE
            # =================================================

            for device_row in devices:
                device = dict(
                    device_row
                )

                device_id = device[
                    "device_id"
                ]

                # ---------------------------------------------
                # Assigned sensor profile
                # ---------------------------------------------

                profile = (
                    load_device_profile_for_live_telemetry(
                        conn,
                        device_id,
                    )
                )

                profile_metadata = (
                    build_profile_live_metadata(
                        profile
                    )
                )

                # ---------------------------------------------
                # Capabilities
                # ---------------------------------------------

                if profile_metadata:
                    capabilities = (
                        profile_metadata[
                            "capabilities"
                        ]
                    )

                else:
                    try:
                        capabilities = (
                            get_device_capabilities_list(
                                conn,
                                device_id,
                                device.get(
                                    "node_type"
                                ),
                            )
                        )

                    except Exception:
                        capabilities = [
                            device.get(
                                "node_type"
                            )
                        ]

                capabilities = [
                    capability
                    for capability in capabilities
                    if capability
                ]

                # ---------------------------------------------
                # ThingsBoard telemetry
                # ---------------------------------------------

                try:
                    tb_telemetry = (
                        read_tb_latest_telemetry(
                            device_id,
                            profile=profile,
                        )
                        or {}
                    )

                except Exception as exc:
                    print(
                        "ThingsBoard telemetry failed "
                        "in floor live:",
                        exc,
                    )

                    tb_telemetry = {}

                # ---------------------------------------------
                # Local validated telemetry
                # ---------------------------------------------

                try:
                    local_telemetry = (
                        get_local_latest_telemetry(
                            conn,
                            device_id,
                        )
                        or {}
                    )

                except Exception as exc:
                    print(
                        "Local telemetry failed "
                        "in floor live:",
                        exc,
                    )

                    local_telemetry = {}

                # ---------------------------------------------
                # Merge both sources
                # ---------------------------------------------

                telemetry = (
                    merge_profile_live_telemetry_sources(
                        tb_telemetry,
                        local_telemetry,
                    )
                )

                # All fields declared by the selected profile.
                telemetry_fields = (
                    build_profile_live_field_metadata(
                        profile,
                        surface="all",
                    )
                )

                # Only fields enabled for Floor Live View.
                floor_display_telemetry = (
                    build_profile_display_telemetry(
                        profile,
                        telemetry,
                        surface="floor",
                    )
                )

                # ---------------------------------------------
                # Build device response
                # ---------------------------------------------

                device["node_type"] = (
                    profile.get(
                        "node_type"
                    )
                    if profile
                    else device.get(
                        "node_type"
                    )
                )

                device["capabilities"] = (
                    capabilities
                )

                device["profile_assigned"] = (
                    bool(profile)
                )

                device["profile"] = (
                    profile_metadata
                )

                device["profile_id"] = (
                    profile.get("id")
                    if profile
                    else device.get(
                        "profile_id"
                    )
                )

                device["profile_code"] = (
                    profile.get(
                        "profile_code"
                    )
                    if profile
                    else device.get(
                        "profile_code"
                    )
                )

                device["profile_version"] = (
                    profile.get(
                        "profile_version"
                    )
                    if profile
                    else device.get(
                        "profile_version"
                    )
                )

                device["payload_version"] = (
                    profile.get(
                        "payload_version"
                    )
                    if profile
                    else device.get(
                        "payload_version"
                    )
                )

                device["icon_type"] = (
                    profile.get(
                        "icon_type"
                    )
                    if (
                        profile
                        and profile.get(
                            "icon_type"
                        )
                    )
                    else device.get(
                        "icon_type"
                    )
                )

                device["icon_color"] = (
                    profile.get(
                        "icon_color"
                    )
                    if profile
                    else None
                )

                device["telemetry"] = (
                    telemetry
                )

                device["telemetry_fields"] = (
                    telemetry_fields
                )

                device[
                    "display_telemetry"
                ] = floor_display_telemetry

                room_obj["devices"].append(
                    device
                )

            result["rooms"].append(
                room_obj
            )

        # =====================================================
        # 5. LOAD FLOOR GATEWAYS
        # =====================================================

        try:
            gateway_rows = conn.execute(
                """
                SELECT *
                FROM gateways
                WHERE floor_id = ?
                ORDER BY name
                """,
                (floor_id,),
            ).fetchall()

            result["gateways"] = [
                dict(gateway)
                for gateway in gateway_rows
            ]

        except Exception as exc:
            print(
                "Gateway loading failed "
                "in floor live:",
                exc,
            )

            result["gateways"] = []

        return result

    finally:
        conn.close()

@router.delete("/buildings/{building_id}/polygon")
def delete_building_polygon(building_id: int):
    conn = db()

    cur = conn.execute("""
        UPDATE buildings
        SET polygon_points = ?,
            x = NULL,
            y = NULL
        WHERE id = ?
    """, (
        json.dumps([]),
        building_id,
    ))

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        raise HTTPException(status_code=404, detail="Building not found")

    return {
        "status": "polygon_deleted",
        "building_id": building_id,
    }

@router.get("/buildings/{building_id}/overview")
def get_building_overview(building_id: int):

    conn = db()

    building = conn.execute("""
        SELECT *
        FROM buildings
        WHERE id = ?
    """, (building_id,)).fetchone()

    if not building:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Building not found"
        )

    floors = conn.execute("""
        SELECT *
        FROM floors
        WHERE building_id = ?
        ORDER BY floor_number
    """, (building_id,)).fetchall()

    result = {
        "building": dict(building),
        "floors": [dict(f) for f in floors]
    }

    conn.close()

    return result

@router.get("/floor-live-view", response_class=HTMLResponse)
def floor_live_view():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Floor Live View</title>

<style>
body{
    margin:0;
    font-family:Arial, sans-serif;
    background:#0f172a;
    color:#e5e7eb;
}

/* Header like Admin Home */
.header{
    padding:24px 34px;
    background:#111827;
    border-bottom:1px solid #334155;
}

.header h1{
    margin:0;
    font-size:28px;
    color:#f8fafc;
}

.header p{
    margin:8px 0 0;
    color:#94a3b8;
    font-size:15px;
}

/* Top controls */
.toolbar{
    padding:16px 34px;
    background:#0f172a;
    border-bottom:1px solid #1e293b;
    display:flex;
    gap:12px;
    align-items:center;
    flex-wrap:wrap;
}

.toolbar label{
    color:#cbd5e1;
    font-weight:bold;
}

.toolbar input{
    width:110px;
    padding:10px 12px;
    border-radius:8px;
    border:1px solid #334155;
    background:#020617;
    color:white;
    outline:none;
}

.toolbar input:focus{
    border-color:#60a5fa;
}

.toolbar button{
    padding:10px 14px;
    border:none;
    border-radius:8px;
    cursor:pointer;
    font-weight:bold;
    color:white;
}

.adminHomeBtn{
    background:#334155;
}

.adminHomeBtn:hover{
    background:#475569;
}

.loadBtn{
    background:#2563eb;
}

.loadBtn:hover{
    background:#1d4ed8;
}

/* Main map area */
.viewer{
    position:relative;
    margin:24px 34px;
    background:#111827;
    border:1px solid #334155;
    border-radius:16px;
    padding:16px;
    box-shadow:0 16px 40px rgba(0,0,0,0.35);
    overflow:hidden;
}

#floorImage{
    width:100%;
    height:auto;
    display:block;
    border:1px solid #334155;
    border-radius:12px;
    background:#020617;
    opacity:0.92;
}

#overlay{
    position:absolute;
    top:16px;
    left:16px;
    width:calc(100% - 32px);
    height:calc(100% - 32px);
    pointer-events:none;
}

/* Rooms */
.room-normal{
    fill:rgba(37,99,235,0.18);
    stroke:#60a5fa;
    stroke-width:3;
}

.room-alarm{
    fill:rgba(239,68,68,0.25);
    stroke:#ef4444;
    stroke-width:4;
}

.room-label{
    fill:#93c5fd;
    font-size:15px;
    font-weight:bold;
    paint-order:stroke;
    stroke:#020617;
    stroke-width:3px;
}

/* Device markers */
.node{
    position:absolute;
    transform:translate(-50%, -50%);
    padding:8px 12px;
    border-radius:999px;
    color:white;
    font-weight:bold;
    font-size:12px;
    cursor:pointer;
    z-index:10;
    box-shadow:0 8px 20px rgba(0,0,0,.45);
    white-space:nowrap;
    border:1px solid rgba(255,255,255,0.25);
}

.node-green{
    background:#16a34a;
}

.node-red{
    background:#dc2626;
}

/* Gateway markers */
.gateway-live-marker{
    position:absolute;
    transform:translate(-50%, -50%);
    width:42px;
    height:42px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-size:20px;
    cursor:pointer;
    z-index:12;
    box-shadow:0 10px 24px rgba(0,0,0,.5);
    border:2px solid rgba(255,255,255,0.35);
}

.gateway-live-marker.online{
    background:#16a34a;
}

.gateway-live-marker.offline{
    background:#64748b;
}

.gateway-live-marker.error{
    background:#dc2626;
}

.gateway-live-marker.unknown{
    background:#f97316;
}

/* Details side panel */
#sidePanel{
    position:fixed;
    top:0;
    right:-390px;
    width:350px;
    height:100vh;
    background:#111827;
    color:#e5e7eb;
    border-left:1px solid #334155;
    box-shadow:-8px 0 30px rgba(0,0,0,.45);
    padding:20px;
    transition:.3s;
    z-index:1000;
    overflow:auto;
}

#sidePanel.open{
    right:0;
}

#sidePanel h2{
    color:#f8fafc;
    margin-top:4px;
}

#sidePanel h3{
    color:#93c5fd;
}

.closeBtn{
    float:right;
    background:#dc2626;
    color:white;
    border:none;
    padding:7px 11px;
    border-radius:8px;
    cursor:pointer;
    font-weight:bold;
}

.closeBtn:hover{
    background:#b91c1c;
}

.infoRow{
    margin:9px 0;
    padding:8px 10px;
    background:#020617;
    border:1px solid #334155;
    border-radius:8px;
    font-size:14px;
}

.infoRow b{
    color:#cbd5e1;
}

.muted{
    color:#94a3b8;
}

.alarmText{
    color:#ef4444;
    font-weight:bold;
}

hr{
    border:none;
    border-top:1px solid #334155;
    margin:16px 0;
}

@media(max-width:900px){
    .toolbar{
        padding:14px 18px;
    }

    .header{
        padding:20px 18px;
    }

    .viewer{
        margin:18px;
        padding:12px;
    }

    #overlay{
        top:12px;
        left:12px;
        width:calc(100% - 24px);
        height:calc(100% - 24px);
    }
}
</style>
</head>

<body>

<div class="toolbar">
    <button class="adminHomeBtn" onclick="window.location.href='/admin'">
        ← Admin Home
    </button>

    <label>Floor:</label>
    <select id="floorId" onchange="loadFloor()"></select>
        Load Floor
    </button>
</div>

<div class="viewer" id="viewer">
    <img id="floorImage">
    <svg id="overlay"></svg>
    <div id="nodesLayer"></div>
</div>

<div id="sidePanel">
    <button class="closeBtn" onclick="closePanel()">X</button>
    <h2 id="panelTitle">Device</h2>
    <div id="panelBody"></div>
</div>

<script>
let floorData = null;

const image = document.getElementById("floorImage");
const overlay = document.getElementById("overlay");
const nodesLayer = document.getElementById("nodesLayer");
const panel = document.getElementById("sidePanel");

function valueOrDash(v){
    if(v === null || v === undefined || v === "") return "--";
    return v;
}

function isTrue(v){
    return v === true || v === "true" || v === "True" || v === 1 || v === "1";
}

function isAlarm(device){
    const t = device.telemetry || {};
    return isTrue(t.alarm_active);
}

function iconFor(type){
    if(type === "environment") return "🌡";
    if(type === "occupancy") return "👤";
    if(type === "safety") return "🔥";
    if(type === "energy") return "⚡";
    return "📡";
}

function originalToDisplay(p){
    return {
        x: p.x * image.clientWidth / floorData.floor.image_width,
        y: p.y * image.clientHeight / floorData.floor.image_height
    };
}

function drawRooms(){
    overlay.innerHTML = "";

    floorData.rooms.forEach(room => {
        if(!room.polygon_points || room.polygon_points.length < 3) return;

        const hasAlarm = room.devices.some(d => isAlarm(d));

        const displayPoints = room.polygon_points.map(originalToDisplay);

        const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        poly.setAttribute("points", displayPoints.map(p => `${p.x},${p.y}`).join(" "));
        poly.setAttribute("class", hasAlarm ? "room-alarm" : "room-normal");
        overlay.appendChild(poly);

        const center = originalToDisplay({x: room.x, y: room.y});

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", center.x);
        text.setAttribute("y", center.y);
        text.setAttribute("class", "room-label");
        text.textContent = room.room_name;
        overlay.appendChild(text);
    });
}


function drawNodes(){
    nodesLayer.innerHTML = "";

    floorData.rooms.forEach(room => {
        room.devices.forEach(device => {
            const node = document.createElement("div");

            const px = device.x || room.x;
            const py = device.y || room.y;
            const pos = originalToDisplay({x:px, y:py});

            node.className = "node " + (isAlarm(device) ? "node-red" : "node-green");
            node.style.left = pos.x + "px";
            node.style.top = pos.y + "px";

            node.innerText =
                iconFor(device.node_type) + " " + (device.label || device.device_id);

            node.onclick = function(e){
                e.stopPropagation();
                openPanel(device, room);
            };

            nodesLayer.appendChild(node);

            applyLatestTelemetryColor(node, device);
        });
    });
}

async function applyLatestTelemetryColor(node, device){
    try {
        const res = await fetch(`/devices/${device.device_id}/latest-telemetry`);

        if (!res.ok) return;

        const data = await res.json();
        const telemetry = data.telemetry || {};

        const batteryStatus = telemetry.battery_status;
        const alarmActive = data.alarm_active === 1 || data.alarm_active === true;

        node.classList.remove("node-green", "node-orange", "node-red");

        if (alarmActive || batteryStatus === "critical") {
            node.classList.add("node-red");
        }

        else if (batteryStatus === "low") {
            node.classList.add("node-orange");
        }

        else {
            node.classList.add("node-green");
        }

        if (batteryStatus) {
            node.title =
                (device.label || device.device_id) +
                " | Battery: " +
                (telemetry.battery_percent || "--") +
                "% | Status: " +
                batteryStatus;
        }

    } catch (e) {
        console.log("Could not load node battery color", e);
    }
}


function hasCapability(device, capability){
    const caps = device.capabilities || [];

    if(caps.includes(capability)) return true;

    return device.node_type === capability;
}

function escapeHtml(value){
    if(value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function formatPlainTelemetryValue(value){
    if(
        value === null ||
        value === undefined ||
        value === ""
    ){
        return "--";
    }

    if(Array.isArray(value)){
        return escapeHtml(
            value.join(", ")
        );
    }

    if(typeof value === "object"){
        try{
            return escapeHtml(
                JSON.stringify(value)
            );
        }
        catch(error){
            return "--";
        }
    }

    return escapeHtml(value);
}


function formatBooleanTelemetryValue(value){
    if(
        value === true ||
        value === "true" ||
        value === "True" ||
        value === 1 ||
        value === "1"
    ){
        return "YES";
    }

    if(
        value === false ||
        value === "false" ||
        value === "False" ||
        value === 0 ||
        value === "0"
    ){
        return "NO";
    }

    return "--";
}


function formatValueWithUnit(value, unit){
    if(
        value === null ||
        value === undefined ||
        value === ""
    ){
        return "--";
    }

    const formattedValue =
        formatPlainTelemetryValue(value);

    if(!unit){
        return formattedValue;
    }

    return (
        formattedValue +
        " " +
        escapeHtml(unit)
    );
}


function formatProfileFieldValue(
    field,
    telemetry
){
    const fieldKey =
        field.field_key;

    let value = field.value;

    if(
        telemetry &&
        Object.prototype.hasOwnProperty.call(
            telemetry,
            fieldKey
        )
    ){
        value = telemetry[fieldKey];
    }

    const dataType = String(
        field.data_type || ""
    ).toLowerCase();

    if(dataType === "boolean"){
        return formatBooleanTelemetryValue(
            value
        );
    }

    const precision =
        field.precision_digits;

    if(
        value !== null &&
        value !== undefined &&
        value !== "" &&
        precision !== null &&
        precision !== undefined &&
        Number.isFinite(Number(value))
    ){
        value = Number(value).toFixed(
            Number(precision)
        );
    }

    return formatValueWithUnit(
        value,
        field.unit
    );
}


function colorForDeviceState(value){
    const state = String(
        value || ""
    ).toLowerCase();

    if(
        state === "critical" ||
        state === "poor" ||
        state === "offline" ||
        state === "alarm" ||
        state === "active"
    ){
        return "#ef4444";
    }

    if(
        state === "low" ||
        state === "marginal" ||
        state === "warning" ||
        state === "unknown"
    ){
        return "#f97316";
    }

    if(
        state === "normal" ||
        state === "good" ||
        state === "online" ||
        state === "ok"
    ){
        return "#22c55e";
    }

    return "#cbd5e1";
}


function buildStaticDeviceHtml(
    device,
    room,
    telemetry
){
    const t = telemetry || {};

    const statusIcon =
        t.device_status === "online"
        ? "🟢"
        : "🔴";

    const profile =
        device.profile || null;

    let profileText = "--";

    if(profile){
        profileText =
            (
                profile.profile_name ||
                profile.profile_code ||
                "--"
            );

        if(profile.profile_version){
            profileText +=
                " / Version " +
                profile.profile_version;
        }
    }
    else if(device.profile_code){
        profileText =
            device.profile_code;

        if(device.profile_version){
            profileText +=
                " / Version " +
                device.profile_version;
        }
    }

    return (
        `<div class="infoRow">
            <b>Device ID:</b>
            ${escapeHtml(device.device_id)}
        </div>` +

        `<div class="infoRow">
            <b>Room:</b>
            ${escapeHtml(
                room.room_name || "--"
            )}
        </div>` +

        `<div class="infoRow">
            <b>Type:</b>
            ${escapeHtml(
                device.node_type || "--"
            )}
        </div>` +

        `<div class="infoRow">
            <b>Sensor Profile:</b>
            ${escapeHtml(profileText)}
        </div>` +

        `<hr>` +

        `<div class="infoRow">
            <b>Status:</b>
            ${statusIcon}
            ${escapeHtml(
                valueOrDash(
                    t.device_status
                )
            )}
        </div>` +

        `<div class="infoRow">
            <b>Last Seen:</b>
            ${escapeHtml(
                valueOrDash(
                    t.last_seen_iso
                )
            )}
        </div>` +

        `<div class="infoRow">
            <b>Last Update:</b>
            ${escapeHtml(
                valueOrDash(
                    t.last_seen_seconds_ago
                )
            )}
            sec ago
        </div>`
    );
}


function buildTelemetryHtml(
    device,
    telemetryOverride = null
){
    const telemetry = Object.assign(
        {},
        device.telemetry || {},
        telemetryOverride || {}
    );

    let html = "";

    const capabilities =
        Array.isArray(device.capabilities)
        ? device.capabilities
        : [];

    html += `
        <div class="infoRow">
            <b>Capabilities:</b>
            ${
                capabilities.length
                ? escapeHtml(
                    capabilities.join(", ")
                )
                : escapeHtml(
                    device.node_type || "--"
                )
            }
        </div>
    `;

    // =====================================================
    // PROFILE-DRIVEN SENSOR READINGS
    // =====================================================

    let displayFields = [];

    if(
        Array.isArray(
            device.display_telemetry
        ) &&
        device.display_telemetry.length
    ){
        displayFields =
            device.display_telemetry;
    }
    else if(
        Array.isArray(
            device.telemetry_fields
        )
    ){
        displayFields =
            device.telemetry_fields.filter(
                field =>
                    field.visible_floor === true ||
                    field.visible_floor === 1
            );
    }

    html += `
        <hr>
        <h3>Sensor Readings</h3>
    `;

    if(displayFields.length === 0){
        html += `
            <p class="muted">
                No Floor Live sensor fields are enabled
                in the assigned profile.
            </p>
        `;
    }
    else{
        displayFields.forEach(field => {
            const label =
                field.label ||
                String(
                    field.field_key || ""
                )
                .replace(/_/g, " ")
                .replace(
                    /\\b\\w/g,
                    character =>
                        character.toUpperCase()
                );

            const formattedValue =
                formatProfileFieldValue(
                    field,
                    telemetry
                );

            html += `
                <div class="infoRow">
                    <b>${escapeHtml(label)}:</b>
                    ${formattedValue}
                </div>
            `;
        });
    }

    // =====================================================
    // DEVICE HEALTH — PRESERVED FOR EVERY SENSOR PROFILE
    // =====================================================

    const batteryStatus =
        telemetry.battery_status;

    const batteryColor =
        colorForDeviceState(
            batteryStatus
        );

    const signalStatus =
        telemetry.signal_status;

    const signalColor =
        colorForDeviceState(
            signalStatus
        );

    html += `
        <hr>
        <h3>Device Health</h3>

        <div class="infoRow">
            <b>Battery Status:</b>
            <span
                style="
                    color:${batteryColor};
                    font-weight:bold;
                "
            >
                ${
                    batteryStatus
                    ? escapeHtml(
                        String(
                            batteryStatus
                        ).toUpperCase()
                    )
                    : "--"
                }
            </span>
        </div>

        <div class="infoRow">
            <b>Battery:</b>
            🔋
            ${formatValueWithUnit(
                telemetry.battery_percent,
                "%"
            )}
        </div>

        <div class="infoRow">
            <b>Battery Voltage:</b>
            ${formatValueWithUnit(
                telemetry.battery_voltage,
                "V"
            )}
        </div>

        <div class="infoRow">
            <b>Power Source:</b>
            ${formatPlainTelemetryValue(
                telemetry.power_source
            )}
        </div>

        <hr>

        <div class="infoRow">
            <b>Signal Quality:</b>
            <span
                style="
                    color:${signalColor};
                    font-weight:bold;
                "
            >
                ${
                    signalStatus
                    ? escapeHtml(
                        String(
                            signalStatus
                        ).toUpperCase()
                    )
                    : "--"
                }
            </span>
        </div>

        <div class="infoRow">
            <b>RSSI:</b>
            ${formatValueWithUnit(
                telemetry.rssi,
                "dBm"
            )}
        </div>

        <div class="infoRow">
            <b>SNR:</b>
            ${formatValueWithUnit(
                telemetry.snr,
                "dB"
            )}
        </div>

        <div class="infoRow">
            <b>Gateway:</b>
            ${formatPlainTelemetryValue(
                telemetry.gateway_id
            )}
        </div>

        <div class="infoRow">
            <b>Received by Gateways:</b>
            ${formatPlainTelemetryValue(
                telemetry.received_by_gateways
            )}
        </div>

        <div class="infoRow">
            <b>Spreading Factor:</b>
            ${formatPlainTelemetryValue(
                telemetry.spreading_factor
            )}
        </div>

        <div class="infoRow">
            <b>Bandwidth:</b>
            ${formatValueWithUnit(
                telemetry.bandwidth,
                "Hz"
            )}
        </div>

        <div class="infoRow">
            <b>Frequency:</b>
            ${formatValueWithUnit(
                telemetry.frequency,
                "Hz"
            )}
        </div>

        <div class="infoRow">
            <b>Telemetry Source:</b>
            ${formatPlainTelemetryValue(
                telemetry.telemetry_source
            )}
        </div>
    `;

    // =====================================================
    // CONFIGURATION INFORMATION
    // =====================================================

    html += `
        <hr>
        <h3>Configuration</h3>

        <div class="infoRow">
            <b>Firmware Version:</b>
            ${formatPlainTelemetryValue(
                telemetry.firmware_version ||
                device.firmware_version
            )}
        </div>

        <div class="infoRow">
            <b>Configuration Status:</b>
            ${formatPlainTelemetryValue(
                device.configuration_status
            )}
        </div>

        <div class="infoRow">
            <b>Profile Version:</b>
            ${formatPlainTelemetryValue(
                device.profile_version
            )}
        </div>

        <div class="infoRow">
            <b>Payload Version:</b>
            ${formatPlainTelemetryValue(
                device.payload_version
            )}
        </div>
    `;

    // =====================================================
    // ALARM STATUS — PRESERVED
    // =====================================================

    const alarmActive =
        isTrue(
            telemetry.alarm_active
        );

    const alarmColor =
        alarmActive
        ? "#ef4444"
        : "#22c55e";

    html += `
        <hr>
        <h3>Alarm Status</h3>

        <div class="infoRow">
            <b>Alarm:</b>
            <span
                style="
                    color:${alarmColor};
                    font-weight:bold;
                "
            >
                ${escapeHtml(
                    telemetry.alarm_message ||
                    "OK"
                )}
            </span>
        </div>

        <div class="infoRow">
            <b>Active Profile Alarms:</b>
            ${formatPlainTelemetryValue(
                telemetry
                    .profile_alarm_active_count
            )}
        </div>

        <div class="infoRow">
            <b>Active Rule Codes:</b>
            ${formatPlainTelemetryValue(
                telemetry
                    .profile_alarm_rule_codes
            )}
        </div>

        <div class="infoRow">
            <b>Telemetry Last Update:</b>
            ${formatPlainTelemetryValue(
                telemetry.telemetry_updated_at ||
                telemetry.local_updated_at ||
                telemetry.last_seen_iso
            )}
        </div>
    `;

    return html;
}


async function openPanel(
    device,
    room
){
    selectedDeviceId =
        device.device_id;

    selectedRoomId =
        room.id;

    document.getElementById(
        "panelTitle"
    ).innerText =
        iconFor(
            device.node_type
        ) +
        " " +
        (
            device.label ||
            device.device_id
        );

    let mergedTelemetry =
        Object.assign(
            {},
            device.telemetry || {}
        );

    function renderPanel(
        messageHtml = ""
    ){
        const staticHtml =
            buildStaticDeviceHtml(
                device,
                room,
                mergedTelemetry
            );

        const telemetryHtml =
            buildTelemetryHtml(
                device,
                mergedTelemetry
            );

        document.getElementById(
            "panelBody"
        ).innerHTML =
            staticHtml +
            telemetryHtml +
            messageHtml;

        panel.classList.add(
            "open"
        );
    }

    // Immediately display the data returned by Floor Live.
    renderPanel(`
        <p class="muted">
            Refreshing latest device telemetry...
        </p>
    `);

    try{
        const response = await fetch(
            `/devices/${
                encodeURIComponent(
                    device.device_id
                )
            }/latest-telemetry`
        );

        if(!response.ok){
            renderPanel(`
                <p class="muted">
                    Latest telemetry could not be refreshed.
                    Showing the most recent Floor Live data.
                </p>
            `);

            return;
        }

        const data =
            await response.json();

        const latestTelemetry =
            (
                data.telemetry &&
                typeof data.telemetry === "object"
            )
            ? data.telemetry
            : {};

        // Preserve Floor Live signal and gateway data while
        // allowing the latest local values to overwrite matching
        // sensor or battery fields.
        mergedTelemetry = Object.assign(
            {},
            mergedTelemetry,
            latestTelemetry
        );

        if(
            data.alarm_active !== undefined
        ){
            mergedTelemetry.alarm_active =
                data.alarm_active;
        }

        if(
            data.alarm_message !== undefined
        ){
            mergedTelemetry.alarm_message =
                data.alarm_message;
        }

        if(data.updated_at){
            mergedTelemetry
                .telemetry_updated_at =
                data.updated_at;
        }

        device.telemetry =
            mergedTelemetry;

        renderPanel();
    }
    catch(error){
        console.log(
            "Telemetry loading error",
            error
        );

        renderPanel(`
            <p class="muted">
                Telemetry refresh failed.
                Showing the most recent Floor Live data.
            </p>
        `);
    }
}

function closePanel(){
    panel.classList.remove("open");
}

function refreshOpenPanel(){
    if(!selectedDeviceId) return;

    let foundDevice = null;
    let foundRoom = null;

    floorData.rooms.forEach(room => {
        room.devices.forEach(device => {
            if(device.device_id === selectedDeviceId){
                foundDevice = device;
                foundRoom = room;
            }
        });
    });

    if(foundDevice && foundRoom){
        openPanel(foundDevice, foundRoom);
    }
}

function drawGateways(){
    document.querySelectorAll(".gateway-live-marker").forEach(el => el.remove());

    if(!floorData.gateways) return;

    const floor = floorData.floor;

    floorData.gateways.forEach(gw => {
        if(gw.x === null || gw.y === null) return;

        const marker = document.createElement("div");
        const status = gw.status || "unknown";

        marker.className = "gateway-live-marker " + status;
        marker.innerHTML = "📡";
        marker.title = gw.label || gw.name || gw.gateway_id;

        marker.style.left = (gw.x * image.clientWidth / floor.image_width) + "px";
        marker.style.top = (gw.y * image.clientHeight / floor.image_height) + "px";

        marker.onclick = function(event){
            event.stopPropagation();

            alert(
                "Gateway: " + (gw.label || gw.name || gw.gateway_id) + "\\n" +
                "Status: " + status + "\\n" +
                "Gateway ID: " + gw.gateway_id + "\\n" +
                "Last seen: " + (gw.last_seen || "--") + "\\n" +
                "Position: X " + gw.x + " / Y " + gw.y + "\\n" +
                "Note: " + (gw.location_note || "--")
            );
        };

        document.querySelector(".viewer").appendChild(marker);
    });
}



async function loadFloor(){
    const floorId = document.getElementById("floorId").value;

    if (!floorId) {
        return;
    }

    const res = await fetch(`/floors/${floorId}/live`);
    floorData = await res.json();

    image.src = floorData.floor.image_path;

    image.onload = function(){
        overlay.setAttribute("width", image.clientWidth);
        overlay.setAttribute("height", image.clientHeight);

        drawRooms();
        drawNodes();
        drawGateways();
        refreshOpenPanel();

    };

    if(image.complete){
        drawRooms();
        drawNodes();
        refreshOpenPanel();
    }
}

setInterval(() => {
    if(document.getElementById("floorId").value){
        loadFloor();
    }
}, 5000);

async function loadFloorDropdown() {
    const select = document.getElementById("floorId");

    try {
        const res = await fetch("/floors");
        const floors = await res.json();

        select.innerHTML = `<option value="">Select floor</option>`;

        floors.forEach(floor => {
            const label = `${floor.name || "Floor"} / Building ID ${floor.building_id} / ID ${floor.id}`;

            select.innerHTML += `
                <option value="${floor.id}">
                    ${label}
                </option>
            `;
        });

        const params = new URLSearchParams(window.location.search);
        const requestedFloorId = params.get("floor_id");

        if (
            requestedFloorId &&
            floors.some(floor => String(floor.id) === String(requestedFloorId))
        ) {
            select.value = requestedFloorId;
            loadFloor();
        }
        else if (floors.length > 0) {
            select.value = floors[0].id;
            loadFloor();
        }

    } catch (err) {
        alert("Could not load floors: " + err.message);
    }
}

window.onload = loadFloorDropdown;
</script>

</body>
</html>
"""

@router.get("/building-overview", response_class=HTMLResponse)
def building_overview():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Building Overview</title>

<style>
body{
    font-family:Arial;
    margin:20px;
    background:#f5f5f5;
}

.card{
    background:white;
    padding:15px;
    margin-bottom:15px;
    border-radius:10px;
    box-shadow:0 2px 10px rgba(0,0,0,.15);
}

.floorBtn{
    display:block;
    width:100%;
    padding:12px;
    margin-top:10px;
    border:none;
    border-radius:8px;
    cursor:pointer;
    background:#1976d2;
    color:white;
    font-weight:bold;
}
</style>
</head>

<body>

<div id="content"></div>

<script>

const params =
    new URLSearchParams(window.location.search);

const buildingId =
    params.get("building_id");

async function loadBuilding(){

    const res =
        await fetch(
            `/buildings/${buildingId}/overview`
        );

    const data =
        await res.json();

    let html = `
        <div class="card">
            <h1>${data.building.name}</h1>
            <p>Building ID: ${data.building.id}</p>
        </div>
    `;

    data.floors.forEach(floor => {

        html += `
            <div class="card">

                <h3>${floor.name}</h3>

                <button
                    class="floorBtn"
                    onclick="
                        window.location.href=
                        '/floor-live-view?floor_id=${floor.id}'
                    "
                >
                    Open Floor
                </button>

            </div>
        `;
    });

    document.getElementById("content")
        .innerHTML = html;
}

loadBuilding();

</script>

</body>
</html>
"""

@router.delete("/rooms/{room_id}")
def delete_room(room_id: int):
    conn = db()

    room = conn.execute("""
        SELECT *
        FROM rooms
        WHERE id = ?
    """, (room_id,)).fetchone()

    if not room:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Room not found"
        )

    devices_count = conn.execute("""
        SELECT COUNT(*)
        FROM devices
        WHERE room_id = ?
    """, (room_id,)).fetchone()[0]

    conn.execute("""
        UPDATE devices
        SET room_id = NULL,
            room = NULL,
            x = NULL,
            y = NULL
        WHERE room_id = ?
    """, (room_id,))

    conn.execute("""
        DELETE FROM rooms
        WHERE id = ?
    """, (room_id,))

    conn.commit()
    conn.close()

    return {
        "status": "deleted",
        "room_id": room_id,
        "devices_preserved_and_unassigned": devices_count
    }

@router.put("/rooms/{room_id}")
def update_room(room_id: int, data: dict):
    room_name = data.get("room_name", "").strip()
    polygon_points = data.get("polygon_points", None)

    if not room_name:
        raise HTTPException(status_code=400, detail="room_name required")

    conn = db()

    room = conn.execute("""
        SELECT *
        FROM rooms
        WHERE id = ?
    """, (room_id,)).fetchone()

    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Room not found")

    if polygon_points is not None:
        if not isinstance(polygon_points, list) or len(polygon_points) < 3:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="polygon_points must contain at least 3 points"
            )

        x_values = [p["x"] for p in polygon_points]
        y_values = [p["y"] for p in polygon_points]

        center_x = int(sum(x_values) / len(x_values))
        center_y = int(sum(y_values) / len(y_values))

        conn.execute("""
            UPDATE rooms
            SET room_name = ?,
                polygon_points = ?,
                x = ?,
                y = ?
            WHERE id = ?
        """, (
            room_name,
            json.dumps(polygon_points),
            center_x,
            center_y,
            room_id,
        ))

    else:
        conn.execute("""
            UPDATE rooms
            SET room_name = ?
            WHERE id = ?
        """, (
            room_name,
            room_id,
        ))

    conn.commit()
    conn.close()

    return {
        "status": "updated",
        "room_id": room_id,
        "room_name": room_name,
    }

@router.get("/floors/{floor_id}/rooms")
def get_floor_rooms(floor_id: int):

    conn = db()

    floor = conn.execute("""
        SELECT *
        FROM floors
        WHERE id = ?
    """, (floor_id,)).fetchone()

    if not floor:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Floor not found"
        )

    rooms = conn.execute("""
        SELECT *
        FROM rooms
        WHERE floor_id = ?
        ORDER BY room_name
    """, (floor_id,)).fetchall()

    result = []

    for room in rooms:

        room_obj = dict(room)

        try:
            room_obj["polygon_points"] = (
                json.loads(room_obj["polygon_points"])
                if room_obj["polygon_points"]
                else []
            )
        except:
            room_obj["polygon_points"] = []

        result.append(room_obj)

    conn.close()

    return result

@router.put("/devices/{device_id}/position")
def update_device_position(
    device_id: str,
    data: dict
):
    x = data.get("x")
    y = data.get("y")
    room_id = data.get("room_id")

    if x is None or y is None:
        raise HTTPException(
            status_code=400,
            detail="x and y are required"
        )

    conn = db()

    device = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    if not device:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    old_device = dict(device)

    if room_id is not None:
        room = conn.execute("""
            SELECT *
            FROM rooms
            WHERE id = ?
            LIMIT 1
        """, (room_id,)).fetchone()

        if not room:
            conn.close()
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )

        conn.execute("""
            UPDATE devices
            SET
                x = ?,
                y = ?,
                room_id = ?
            WHERE device_id = ?
        """, (
            x,
            y,
            room_id,
            device_id
        ))

    else:
        conn.execute("""
            UPDATE devices
            SET
                x = ?,
                y = ?
            WHERE device_id = ?
        """, (
            x,
            y,
            device_id
        ))

    conn.commit()

    updated = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    new_device = dict(updated)

    tracked_fields = [
        "x",
        "y",
        "room_id"
    ]

    changed_fields = {}

    for field in tracked_fields:
        if old_device.get(field) != new_device.get(field):
            changed_fields[field] = {
                "old": old_device.get(field),
                "new": new_device.get(field)
            }

    if changed_fields:
        device_scope = get_device_scope_for_audit(conn, device_id)

        node_label = (
            new_device.get("label")
            or new_device.get("device_id")
            or device_id
        )

        message = (
            f"Node {node_label} was moved from "
            f"({old_device.get('x')}, {old_device.get('y')}) "
            f"to ({new_device.get('x')}, {new_device.get('y')})."
        )

        if old_device.get("room_id") != new_device.get("room_id"):
            message += (
                f" Room changed from {old_device.get('room_id')} "
                f"to {new_device.get('room_id')}."
            )

        log_audit_event(
            conn,
            action="move_device",
            target_type="device",
            target_id=device_id,
            message=message,
            details={
                "changed_fields": changed_fields,
                "old": old_device,
                "new": new_device
            },
            client_id=device_scope.get("client_id"),
            site_id=device_scope.get("site_id"),
            building_id=device_scope.get("building_id"),
            floor_id=device_scope.get("floor_id"),
            room_id=device_scope.get("room_id"),
            device_id=device_scope.get("device_id")
        )

    conn.close()

    return {
        "status": "updated" if changed_fields else "no_change",
        "device_id": device_id,
        "x": x,
        "y": y,
        "room_id": room_id,
        "changed_fields": changed_fields
    }

@router.post("/devices/{device_id}/capabilities")
def set_device_capabilities(
    device_id: str,
    data: dict,
):
    """
    Save capabilities safely.

    Profile-assigned devices are controlled by their sensor profile.
    Legacy devices without a profile temporarily retain the original
    manual-capability behavior.
    """

    capabilities = data.get("capabilities")

    if (
        not isinstance(capabilities, list)
        or len(capabilities) == 0
    ):
        raise HTTPException(
            status_code=400,
            detail="capabilities must be a non-empty list",
        )

    # ---------------------------------------------------------
    # 1. Normalize submitted capability keys
    # ---------------------------------------------------------

    submitted_capabilities = []

    for value in capabilities:
        capability = str(
            value or ""
        ).strip().lower()

        if not capability:
            raise HTTPException(
                status_code=400,
                detail="Capability values cannot be empty",
            )

        if not PROFILE_KEY_PATTERN.fullmatch(
            capability
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid capability key: {capability}"
                ),
            )

        if capability not in submitted_capabilities:
            submitted_capabilities.append(
                capability
            )

    conn = db()

    profile = None
    profile_controlled = False
    final_capabilities = []
    final_node_type = ""
    formatter_mode = ""

    try:
        # -----------------------------------------------------
        # 2. Load the complete device record
        # -----------------------------------------------------

        device_row = conn.execute(
            """
            SELECT *
            FROM devices
            WHERE device_id = ?
            LIMIT 1
            """,
            (device_id,),
        ).fetchone()

        if not device_row:
            raise HTTPException(
                status_code=404,
                detail="Device not found",
            )

        device = dict(device_row)

        profile_identifier = (
            device.get("profile_id")
            or device.get("profile_code")
        )

        # =====================================================
        # 3. PROFILE-CONTROLLED DEVICE
        # =====================================================

        if profile_identifier:
            profile_controlled = True
            formatter_mode = "sensor_profile"

            profile = get_sensor_profile_detail(
                conn,
                profile_identifier,
                include_formatter=True,
            )

            if not profile:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "The assigned sensor profile "
                            "could not be found"
                        ),
                        "device_id": device_id,
                        "profile_id": device.get(
                            "profile_id"
                        ),
                        "profile_code": device.get(
                            "profile_code"
                        ),
                    },
                )

            device_profile_code = str(
                device.get("profile_code") or ""
            ).strip().upper()

            current_profile_code = str(
                profile.get("profile_code") or ""
            ).strip().upper()

            if (
                device_profile_code
                != current_profile_code
            ):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "Device profile assignment does "
                            "not match the profile record"
                        ),
                        "device_profile_code": (
                            device_profile_code
                        ),
                        "database_profile_code": (
                            current_profile_code
                        ),
                    },
                )

            device_profile_version = int(
                device.get("profile_version") or 0
            )

            current_profile_version = int(
                profile.get("profile_version") or 0
            )

            if (
                device_profile_version
                != current_profile_version
            ):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "The device is assigned to an "
                            "older profile version and must "
                            "be reprovisioned"
                        ),
                        "device_profile_version": (
                            device_profile_version
                        ),
                        "current_profile_version": (
                            current_profile_version
                        ),
                    },
                )

            if not bool(profile.get("enabled")):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "The assigned sensor profile is "
                        "disabled"
                    ),
                )

            if (
                str(profile.get("status") or "")
                .strip()
                .lower()
                != "active"
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "The assigned sensor profile is "
                        "not active"
                    ),
                )

            final_capabilities = (
                profile_unique_string_list(
                    profile.get("capabilities", [])
                )
            )

            if not final_capabilities:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "The assigned profile has no "
                        "capabilities"
                    ),
                )

            # Administrators cannot override profile capabilities
            # from the legacy capabilities page.
            if (
                set(submitted_capabilities)
                != set(final_capabilities)
            ):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "Capabilities are controlled by "
                            "the assigned sensor profile"
                        ),
                        "profile_code": (
                            current_profile_code
                        ),
                        "submitted_capabilities": (
                            submitted_capabilities
                        ),
                        "profile_capabilities": (
                            final_capabilities
                        ),
                        "action": (
                            "Edit or assign a different "
                            "sensor profile instead"
                        ),
                    },
                )

            final_node_type = str(
                profile.get("node_type") or ""
            ).strip().lower()

            if not final_node_type:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "The assigned sensor profile has "
                        "no node type"
                    ),
                )

        # =====================================================
        # 4. LEGACY DEVICE WITHOUT PROFILE
        # =====================================================

        else:
            formatter_mode = "legacy_node_type"

            legacy_allowed_capabilities = {
                "environment",
                "energy",
                "safety",
                "occupancy",
            }

            for capability in submitted_capabilities:
                if (
                    capability
                    not in legacy_allowed_capabilities
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Legacy devices support only: "
                            + ", ".join(
                                sorted(
                                    legacy_allowed_capabilities
                                )
                            )
                        ),
                    )

            final_capabilities = (
                submitted_capabilities
            )

            if len(final_capabilities) > 1:
                final_node_type = "multi"
            else:
                final_node_type = (
                    final_capabilities[0]
                )

        # -----------------------------------------------------
        # 5. Replace stored capability rows
        # -----------------------------------------------------

        conn.execute(
            """
            DELETE FROM device_capabilities
            WHERE device_id = ?
            """,
            (device_id,),
        )

        for capability in final_capabilities:
            conn.execute(
                """
                INSERT OR IGNORE INTO
                device_capabilities(
                    device_id,
                    capability
                )
                VALUES (?, ?)
                """,
                (
                    device_id,
                    capability,
                ),
            )

        # For profile-controlled devices, this also repairs any
        # old node-type drift using the canonical profile value.
        conn.execute(
            """
            UPDATE devices
            SET node_type = ?
            WHERE device_id = ?
            """,
            (
                final_node_type,
                device_id,
            ),
        )

        conn.commit()

    except HTTPException:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save device capabilities: "
                f"{exc}"
            ),
        )

    finally:
        conn.close()

    # ---------------------------------------------------------
    # 6. Synchronize the appropriate TTN formatter
    # ---------------------------------------------------------

    formatter_synced = False
    formatter_error = None
    formatter_result = None

    try:
        if profile_controlled:
            formatter_result = (
                set_device_formatter_from_profile(
                    device_id=device_id,
                    profile=profile,
                )
            )

            formatter_synced = True

        else:
            # Temporary compatibility for old devices that have
            # not yet been migrated to sensor profiles.
            if final_node_type in FORMATTERS:
                set_device_formatter(
                    device_id,
                    final_node_type,
                )

                formatter_synced = True

            else:
                formatter_error = (
                    "No legacy formatter found for "
                    f"node_type: {final_node_type}"
                )

    except Exception as exc:
        formatter_error = str(exc)

    return {
        "status": "saved",
        "device_id": device_id,
        "profile_controlled": profile_controlled,
        "profile_code": (
            profile.get("profile_code")
            if profile_controlled
            else None
        ),
        "profile_version": (
            profile.get("profile_version")
            if profile_controlled
            else None
        ),
        "node_type": final_node_type,
        "capabilities": final_capabilities,
        "formatter_mode": formatter_mode,
        "formatter_synced": formatter_synced,
        "formatter_error": formatter_error,
        "formatter_result": formatter_result,
    }

@router.get("/devices/{device_id}/capabilities")
def get_device_capabilities(device_id: str):
    conn = db()

    device = conn.execute("""
        SELECT *
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()

    if not device:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    rows = conn.execute("""
        SELECT capability
        FROM device_capabilities
        WHERE device_id = ?
        ORDER BY capability
    """, (device_id,)).fetchall()

    conn.close()

    return {
        "device_id": device_id,
        "node_type": device["node_type"],
        "capabilities": [r["capability"] for r in rows]
    }

@router.post("/devices/{device_id}/sync-formatter")
def sync_device_formatter(device_id: str):
    """
    Synchronize a TTN formatter using the sensor profile currently
    assigned to the device.
    """

    conn = db()

    try:
        device_row = conn.execute(
            """
            SELECT *
            FROM devices
            WHERE device_id = ?
            LIMIT 1
            """,
            (device_id,),
        ).fetchone()

        if not device_row:
            raise HTTPException(
                status_code=404,
                detail="Device not found",
            )

        device = dict(device_row)

        profile_identifier = (
            device.get("profile_id")
            or device.get("profile_code")
        )

        if not profile_identifier:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Device has no assigned sensor profile"
                    ),
                    "device_id": device_id,
                    "action": (
                        "Provision the device using a sensor "
                        "profile before synchronizing its "
                        "formatter"
                    ),
                },
            )

        profile = get_sensor_profile_detail(
            conn,
            profile_identifier,
            include_formatter=True,
        )

        if not profile:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "The device's assigned sensor profile "
                        "could not be found"
                    ),
                    "device_id": device_id,
                    "profile_id": device.get("profile_id"),
                    "profile_code": device.get(
                        "profile_code"
                    ),
                },
            )

        stored_device_profile_code = str(
            device.get("profile_code") or ""
        ).strip().upper()

        current_profile_code = str(
            profile.get("profile_code") or ""
        ).strip().upper()

        if (
            stored_device_profile_code
            != current_profile_code
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Device profile assignment does not "
                        "match the selected database profile"
                    ),
                    "device_profile_code": (
                        stored_device_profile_code
                    ),
                    "database_profile_code": (
                        current_profile_code
                    ),
                },
            )

        device_profile_version = int(
            device.get("profile_version") or 0
        )

        current_profile_version = int(
            profile.get("profile_version") or 0
        )

        if (
            device_profile_version
            != current_profile_version
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "The device is assigned to an older "
                        "profile version and must be "
                        "reprovisioned"
                    ),
                    "device_profile_version": (
                        device_profile_version
                    ),
                    "current_profile_version": (
                        current_profile_version
                    ),
                },
            )

        if not bool(profile.get("enabled")):
            raise HTTPException(
                status_code=409,
                detail=(
                    "The assigned sensor profile is disabled"
                ),
            )

        if (
            str(profile.get("status") or "")
            .strip()
            .lower()
            != "active"
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "The assigned sensor profile is not active"
                ),
            )

    finally:
        conn.close()

    result = set_device_formatter_from_profile(
        device_id=device_id,
        profile=profile,
    )

    return {
        **result,
        "node_type": device["node_type"],
        "configuration_status": device[
            "configuration_status"
        ],
        "configuration_checksum": device[
            "configuration_checksum"
        ],
    }

@router.get("/admin/summary")
def admin_summary():
    conn = db()

    def count_table(table_name):
        try:
            row = conn.execute(f"SELECT COUNT(*) AS c FROM {table_name}").fetchone()
            return row["c"]
        except Exception:
            return 0

    def parse_datetime_safe(value):
        if not value:
            return None

        text = str(value).strip()

        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))

            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

            return dt
        except Exception:
            pass

        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f"
        ]:
            try:
                return datetime.strptime(text.replace("Z", ""), fmt)
            except Exception:
                pass

        return None

    def is_true(value):
        return value in [True, "true", "True", "1", 1]

    def has_real_tb_telemetry(telemetry):
        if not telemetry:
            return False

        if telemetry.get("last_seen_ts") is not None:
            return True

        useful_keys = [
            "temperature",
            "humidity",
            "motion",
            "alarm",
            "voltage",
            "current",
            "power"
        ]

        for key in useful_keys:
            if telemetry.get(key) is not None:
                return True

        return False

    def thingsboard_available_quick():
        global TB_TOKEN_CACHE

        if not THINGSBOARD_URL:
            return False

        try:
            response = requests.post(
                f"{THINGSBOARD_URL}/api/auth/login",
                json={
                    "username": TB_USERNAME,
                    "password": TB_PASSWORD
                },
                timeout=2
            )

            if response.status_code >= 300:
                return False

            data = response.json()

            if data.get("token"):
                TB_TOKEN_CACHE = data["token"]
                return True

            return False

        except Exception:
            return False

    def read_local_latest_telemetry(device_id):
        row = conn.execute("""
            SELECT *
            FROM device_latest_telemetry
            WHERE device_id = ?
            LIMIT 1
        """, (device_id,)).fetchone()

        if not row:
            return None

        item = dict(row)

        try:
            telemetry = json.loads(item["telemetry"]) if item["telemetry"] else {}
        except Exception:
            telemetry = {}

        telemetry["alarm_active"] = bool(item["alarm_active"])
        telemetry["alarm_message"] = item["alarm_message"]
        telemetry["local_updated_at"] = item["updated_at"]

        return telemetry

    def get_local_device_status(local_telemetry):
        if not local_telemetry:
            return "offline", None

        updated_at = local_telemetry.get("local_updated_at")
        updated_dt = parse_datetime_safe(updated_at)

        if not updated_dt:
            return "offline", updated_at

        now = datetime.now()
        seconds_ago = (now - updated_dt).total_seconds()

        if seconds_ago <= 300:
            return "online", updated_at

        return "offline", updated_at

    total_clients = count_table("clients")
    total_sites = count_table("sites")
    total_buildings = count_table("buildings")
    total_floors = count_table("floors")
    total_rooms = count_table("rooms")

    device_rows = conn.execute("""
        SELECT device_id
        FROM devices
        ORDER BY device_id
    """).fetchall()

    active_alarm_rows = conn.execute("""
        SELECT DISTINCT device_id
        FROM alarm_history
        WHERE resolved = 0
    """).fetchall()

    active_alarm_device_ids = set()

    for row in active_alarm_rows:
        active_alarm_device_ids.add(row["device_id"])

    total_devices = len(device_rows)
    online_devices = 0
    offline_devices = 0
    last_device_seen = None
    device_summary_source = "local_database"

    tb_available = thingsboard_available_quick()

    if tb_available:
        device_summary_source = "thingsboard_with_local_fallback"

    for row in device_rows:
        device_id = row["device_id"]

        local_telemetry = read_local_latest_telemetry(device_id)
        local_status, local_last_seen = get_local_device_status(local_telemetry)

        selected_status = local_status
        selected_last_seen = local_last_seen

        if tb_available:
            try:
                tb_telemetry = read_tb_latest_telemetry(device_id)

                if has_real_tb_telemetry(tb_telemetry):
                    selected_status = tb_telemetry.get("device_status", selected_status)
                    selected_last_seen = tb_telemetry.get("last_seen_iso", selected_last_seen)

            except Exception:
                pass

        if selected_status == "online":
            online_devices += 1
        else:
            offline_devices += 1

        if selected_last_seen:
            selected_dt = parse_datetime_safe(selected_last_seen)

            if selected_dt:
                if last_device_seen is None:
                    last_device_seen = selected_last_seen
                else:
                    current_last_dt = parse_datetime_safe(last_device_seen)

                    if current_last_dt and selected_dt > current_last_dt:
                        last_device_seen = selected_last_seen

    active_alarms = len(active_alarm_device_ids)

    gateway_rows = conn.execute("""
        SELECT *
        FROM gateways
        ORDER BY gateway_id
    """).fetchall()

    total_gateways = len(gateway_rows)
    online_gateways = 0
    offline_gateways = 0
    gateway_errors = 0
    last_gateway_seen = None

    for row in gateway_rows:
        gateway = dict(row)
        status = (gateway.get("status") or "unknown").lower()

        if status == "online":
            online_gateways += 1
        elif status == "error":
            gateway_errors += 1
        else:
            offline_gateways += 1

        gateway_last_seen = gateway.get("last_seen")

        if gateway_last_seen:
            gateway_dt = parse_datetime_safe(gateway_last_seen)

            if gateway_dt:
                if last_gateway_seen is None:
                    last_gateway_seen = gateway_last_seen
                else:
                    current_gateway_dt = parse_datetime_safe(last_gateway_seen)

                    if current_gateway_dt and gateway_dt > current_gateway_dt:
                        last_gateway_seen = gateway_last_seen

    conn.close()

    return {
        "clients": total_clients,
        "sites": total_sites,
        "buildings": total_buildings,
        "floors": total_floors,
        "rooms": total_rooms,

        "data_sources": {
            "thingsboard_available": tb_available,
            "device_summary_source": device_summary_source,
            "gateway_summary_source": "backend_database"
        },

        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": offline_devices,
            "active_alarms": active_alarms,
            "last_seen": last_device_seen
        },

        "gateways": {
            "total": total_gateways,
            "online": online_gateways,
            "offline": offline_gateways,
            "errors": gateway_errors,
            "last_seen": last_gateway_seen
        }
    }

@router.get("/test-token-refresh")
def test_token_refresh():
    global TB_TOKEN_CACHE

    TB_TOKEN_CACHE = "fake_expired_token"

    try:
        r = tb_request("GET", "/api/auth/user")

        return {
            "status": "ok",
            "message": "Token refresh worked automatically",
            "thingsboard_response": r.json(),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
@router.get("/api/devices/{device_id}/history")
def get_device_history(device_id: str):
    conn = db()
    try:
        cursor = conn.execute(
            '''
            SELECT telemetry, timestamp 
            FROM historical_telemetry 
            WHERE device_id = ? 
            ORDER BY timestamp ASC 
            LIMIT 100
            ''', 
            (device_id,)
        )
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "telemetry": json.loads(row["telemetry"]),
                "timestamp": row["timestamp"]
            })
            
        return {"status": "success", "history": history}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        conn.close()


import io
import zipfile
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

@router.get("/api/firmware/generate-sensor-template")
def generate_sensor_template(name: str):
    if not name or not name.isalnum():
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid sensor name. Use alphanumeric characters only."})

    h_content = f'''#ifndef {name.upper()}_SENSOR_MODULE_H
#define {name.upper()}_SENSOR_MODULE_H

#include "SensorModule.h"

class {name}SensorModule : public SensorModule {{
public:
    {name}SensorModule();
    void setup() override;
    void readData() override;
}};

#endif // {name.upper()}_SENSOR_MODULE_H
'''

    cpp_content = f'''#include "{name}SensorModule.h"

{name}SensorModule::{name}SensorModule() : SensorModule("{name}") {{}}

void {name}SensorModule::setup() {{
    // TODO: Initialize hardware here (e.g. Wire.begin(), etc.)
}}

void {name}SensorModule::readData() {{
    // TODO: Read data from sensor
    // addData("temperature", 25.4);
    // addData("humidity", 60.1);
}}
'''

    encoder_content = f'''#include "PayloadEncoder.h"
#include "{name}SensorModule.h"

class {name}Encoder : public PayloadEncoder {{
public:
    void encode(std::vector<uint8_t>& payload, SensorModule* module) override {{
        // TODO: Map module data to LoRaWAN bytes
        // float temp = module->getData("temperature");
        // payload.push_back((uint8_t)temp);
    }}
}};
'''

    instructions = f'''To fully integrate your new {name} sensor:

1. Copy the generated files:
   - {name}SensorModule.h -> src/sensors/
   - {name}SensorModule.cpp -> src/sensors/
   - {name}Encoder.cpp -> src/payloads/

2. Open src/framework/SensorRegistry.cpp and add:
   #include "../sensors/{name}SensorModule.h"
   // Inside registerSensors():
   registry["{name}"] = []() -> SensorModule* {{ return new {name}SensorModule(); }};

3. Open src/framework/PayloadRegistry.cpp and add:
   #include "../payloads/{name}Encoder.cpp"
   // Inside registerEncoders():
   registry["{name}"] = []() -> PayloadEncoder* {{ return new {name}Encoder(); }};

4. Open BuildConfig.h and enable it:
   #define ENABLE_{name.upper()} 1
'''

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr(f"src/sensors/{name}SensorModule.h", h_content)
        zip_file.writestr(f"src/sensors/{name}SensorModule.cpp", cpp_content)
        zip_file.writestr(f"src/payloads/{name}Encoder.cpp", encoder_content)
        zip_file.writestr("instructions.txt", instructions)

    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer, 
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={name}_Firmware_Template.zip"
        }
    )


# ---------------------------------------------------------
# BULK CSV IMPORT
# ---------------------------------------------------------
@router.post("/api/devices/bulk-import")
async def bulk_import_devices(file: UploadFile = File(...)):
    import csv
    import codecs
    
    conn = db()
    cursor = conn.cursor()
    
    csvReader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
    success_count = 0
    errors = []
    
    for row in csvReader:
        try:
            dev_eui = row.get('dev_eui', '').strip().upper()
            app_key = row.get('app_key', '').strip().upper()
            room_id = row.get('room_id', '').strip()
            profile_id = row.get('profile_id', '').strip()
            label = row.get('label', '').strip()
            
            if not dev_eui or not room_id or not profile_id:
                errors.append(f"Row missing required fields: {row}")
                continue
                
            # If app_key is empty, generate a secure random one
            if not app_key:
                app_key = secrets.token_hex(16).upper()
                
            chip_mac = f"BULK-{dev_eui}"
            device_id = f"node-{dev_eui.lower()}"
            
            # Fetch room details
            cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
            room = cursor.fetchone()
            if not room:
                errors.append(f"Room {room_id} not found for {dev_eui}")
                continue
                
            # Fetch profile
            cursor.execute("SELECT * FROM sensor_profiles WHERE id = ?", (profile_id,))
            profile = cursor.fetchone()
            if not profile:
                errors.append(f"Profile {profile_id} not found for {dev_eui}")
                continue
                
            # Insert into database
            cursor.execute("""
                INSERT OR REPLACE INTO devices 
                (chip_mac, device_id, dev_eui, app_key, join_eui, building, floor, room, label, client_id, site_id, building_id, floor_id, room_id, profile_id, profile_code, node_type, configuration_status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'legacy')
            """, (
                chip_mac, device_id, dev_eui, app_key, "0000000000000000",
                room['building'], room['floor'], room['room_name'], label,
                room['client_id'], room['site_id'], room['floor_id'], room['floor_id'], room_id,
                profile_id, profile['profile_code'], profile['module_key']
            ))
            
            cursor.execute("""
                INSERT OR IGNORE INTO device_latest_telemetry (device_id, telemetry)
                VALUES (?, '{}')
            """, (device_id,))
            
            success_count += 1
            
        except Exception as e:
            errors.append(f"Error on {row.get('dev_eui')}: {str(e)}")
            
    conn.commit()
    conn.close()
    
    return JSONResponse(status_code=200, content={
        "status": "success",
        "imported": success_count,
        "errors": errors
    })

# ---------------------------------------------------------
# ANALYTICS DASHBOARD
# ---------------------------------------------------------
@router.get("/api/analytics")
def get_analytics():
    conn = db()
    cursor = conn.cursor()
    
    # Active devices
    cursor.execute("SELECT COUNT(*) as c FROM devices")
    total_devices = cursor.fetchone()['c']
    
    # Offline devices
    cursor.execute("SELECT COUNT(*) as c FROM device_latest_telemetry WHERE alarm_message = 'OFFLINE'")
    offline_devices = cursor.fetchone()['c']
    
    # Gateways
    cursor.execute("SELECT COUNT(*) as c FROM gateways")
    total_gateways = cursor.fetchone()['c']
    
    # Alarms today
    cursor.execute("SELECT COUNT(*) as c FROM alarm_history WHERE timestamp >= date('now')")
    alarms_today = cursor.fetchone()['c']
    
    conn.close()


# ---------------------------------------------------------
# BULK CSV IMPORT
# ---------------------------------------------------------
@router.post("/api/devices/bulk-import")
async def bulk_import_devices(file: UploadFile = File(...)):
    import csv
    import codecs
    
    conn = db()
    cursor = conn.cursor()
    
    csvReader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
    success_count = 0
    errors = []
    
    for row in csvReader:
        try:
            dev_eui = row.get('dev_eui', '').strip().upper()
            app_key = row.get('app_key', '').strip().upper()
            room_id = row.get('room_id', '').strip()
            profile_id = row.get('profile_id', '').strip()
            label = row.get('label', '').strip()
            
            if not dev_eui or not room_id or not profile_id:
                errors.append(f"Row missing required fields: {row}")
                continue
                
            # If app_key is empty, generate a secure random one
            if not app_key:
                app_key = secrets.token_hex(16).upper()
                
            chip_mac = f"BULK-{dev_eui}"
            device_id = f"node-{dev_eui.lower()}"
            
            # Fetch room details
            cursor.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
            room = cursor.fetchone()
            if not room:
                errors.append(f"Room {room_id} not found for {dev_eui}")
                continue
                
            # Fetch profile
            cursor.execute("SELECT * FROM sensor_profiles WHERE id = ?", (profile_id,))
            profile = cursor.fetchone()
            if not profile:
                errors.append(f"Profile {profile_id} not found for {dev_eui}")
                continue
                
            # Insert into database
            cursor.execute("""
                INSERT OR REPLACE INTO devices 
                (chip_mac, device_id, dev_eui, app_key, join_eui, building, floor, room, label, client_id, site_id, building_id, floor_id, room_id, profile_id, profile_code, node_type, configuration_status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'legacy')
            """, (
                chip_mac, device_id, dev_eui, app_key, "0000000000000000",
                room['building'], room['floor'], room['room_name'], label,
                room['client_id'], room['site_id'], room['floor_id'], room['floor_id'], room_id,
                profile_id, profile['profile_code'], profile['module_key']
            ))
            
            cursor.execute("""
                INSERT OR IGNORE INTO device_latest_telemetry (device_id, telemetry)
                VALUES (?, '{}')
            """, (device_id,))
            
            success_count += 1
            
        except Exception as e:
            errors.append(f"Error on {row.get('dev_eui')}: {str(e)}")
            
    conn.commit()
    conn.close()
    
    return JSONResponse(status_code=200, content={
        "status": "success",
        "imported": success_count,
        "errors": errors
    })

# ---------------------------------------------------------
# ANALYTICS DASHBOARD
# ---------------------------------------------------------
@router.get("/api/analytics")
def get_analytics():
    conn = db()
    cursor = conn.cursor()
    
    # Active devices
    cursor.execute("SELECT COUNT(*) as c FROM devices")
    total_devices = cursor.fetchone()['c']
    
    # Offline devices
    cursor.execute("SELECT COUNT(*) as c FROM device_latest_telemetry WHERE alarm_message = 'OFFLINE'")
    offline_devices = cursor.fetchone()['c']
    
    # Gateways
    cursor.execute("SELECT COUNT(*) as c FROM gateways")
    total_gateways = cursor.fetchone()['c']
    
    # Alarms today
    cursor.execute("SELECT COUNT(*) as c FROM alarm_history WHERE timestamp >= date('now')")
    alarms_today = cursor.fetchone()['c']
    
    conn.close()
    
    return {
        "total_devices": total_devices,
        "offline_devices": offline_devices,
        "total_gateways": total_gateways,
        "alarms_today": alarms_today
    }

# ---------------------------------------------------------
# SERVICE WORKER (with proper scope header)
# ---------------------------------------------------------
from fastapi.responses import FileResponse
import os

@router.get("/service-worker.js")
def serve_service_worker():
    sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "service-worker.js")
    return FileResponse(
        sw_path,
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"}
    )
