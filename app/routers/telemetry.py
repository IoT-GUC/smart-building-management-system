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

@router.get("/floor-map-data")
def floor_map_data(building: str, floor: str):
    conn = db()

    floor_row = conn.execute("""
        SELECT f.id as floor_id, f.image_path, f.image_width, f.image_height, b.name as building_name, f.name as floor_name
        FROM floors f
        JOIN buildings b ON f.building_id = b.id
        WHERE b.name = ? AND (f.name = ? OR f.floor_number = ?)
        LIMIT 1
    """, (building, floor, floor)).fetchone()

    if not floor_row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Floorplan not found"
        )

    floor_id = floor_row["floor_id"]

    room_rows = conn.execute("""
        SELECT id, room_name, polygon_points, x, y
        FROM rooms
        WHERE floor_id = ?
        ORDER BY room_name
    """, (floor_id,)).fetchall()

    device_rows = conn.execute("""
        SELECT
            d.device_id,
            d.node_type,
            d.label,
            d.x,
            d.y,
            d.icon_type,
            r.room_name as room
        FROM devices d
        LEFT JOIN rooms r ON d.room_id = r.id
        WHERE r.floor_id = ?
        ORDER BY r.room_name, d.label
    """, (floor_id,)).fetchall()

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
            "building": building,
            "floor": floor,
            "room": row["room"],
            "label": row["label"],
            "x": row["x"],
            "y": row["y"],
            "icon_type": row["icon_type"],
            "telemetry": telemetry,
        })

    return {
        "building": building,
        "floor": floor,
        "image_path": floor_row["image_path"],
        "image_width": floor_row["image_width"],
        "image_height": floor_row["image_height"],
        "rooms": rooms,
        "devices": devices
    }
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
    cursor.execute("SELECT COUNT(*) as c FROM alarm_history WHERE datetime(triggered_at) >= datetime('now', 'start of day')")
    alarms_today = cursor.fetchone()['c']
    
    conn.close()
    
    return {
        "total_devices": total_devices,
        "offline_devices": offline_devices,
        "total_gateways": total_gateways,
        "alarms_today": alarms_today
    }