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
from app.services.uploads import save_image_securely

router = APIRouter()

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

    filename, width, height = await save_image_securely(image, UPLOAD_DIR, prefix=f"floor_{floor_id}")
    image_path = f"/uploads/{filename}"

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
@router.post("/floorplans/upload")
async def upload_floorplan(
    building: str = Form(...),
    floor: str = Form(...),
    image: UploadFile = File(...)
):
    safe_building = re.sub(r"[^a-zA-Z0-9_-]", "_", building)
    safe_floor = re.sub(r"[^a-zA-Z0-9_-]", "_", floor)
    prefix = f"{safe_building}_floor_{safe_floor}"

    filename, width, height = await save_image_securely(image, UPLOAD_DIR, prefix=prefix)
    image_path = f"/uploads/{filename}"

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
            image_path,
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
        "image_path": image_path,
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
        "floor_id",
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
            floor_id,
            room_name,
            polygon_points,
            x,
            y
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["floor_id"],
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
        "floor_id": data["floor_id"],
        "room_name": data["room_name"],
        "polygon_points": polygon_points,
        "x": center_x,
        "y": center_y,
    }
@router.get("/rooms")
def get_rooms(floor_id: int | None = None):
    conn = db()

    if floor_id is not None:
        rows = conn.execute("""
            SELECT id, floor_id, room_name, polygon_points, x, y, created_at
            FROM rooms
            WHERE floor_id = ?
            ORDER BY id DESC
        """, (floor_id,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT id, floor_id, room_name, polygon_points, x, y, created_at
            FROM rooms
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "floor_id": row["floor_id"],
            "room_name": row["room_name"],
            "polygon_points": json.loads(row["polygon_points"]),
            "x": row["x"],
            "y": row["y"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
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
def assign_device_to_room_post(room_id: int, data: dict):

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

    cur = conn.execute("""
        UPDATE devices
        SET
            room_id = ?
        WHERE device_id = ?
    """, (
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

    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", site["name"])
    filename, width, height = await save_image_securely(image, UPLOAD_DIR, prefix=f"site_{site_id}_{safe_name}")
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
                    logger.info(
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
                    logger.info(
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
            logger.info(
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