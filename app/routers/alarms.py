import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.db.connection import get_db_connection as db
from app.main import ADMIN_PASSWORD, get_device_scope_for_audit, log_audit_event

router = APIRouter()

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
    try:

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

        limit = min(limit, 5000)

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
    finally:
        conn.close()
@router.get("/alarms")
def get_alarms(status: str | None = None):
    conn = db()
    try:

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
    finally:
        conn.close()
@router.post("/alarms/{alarm_id}/acknowledge")
def acknowledge_alarm(alarm_id: int, data: dict | None = None):
    acknowledged_by = (data or {}).get("acknowledged_by", "admin")

    conn = db()
    try:

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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
@router.post("/alarms/{alarm_id}/resolve")
def resolve_alarm(alarm_id: int, data: dict | None = None):
    resolved_by = (data or {}).get("resolved_by", "admin")

    conn = db()
    try:

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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
@router.get("/alarm-settings")
def get_alarm_settings():
    conn = db()
    try:

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
    finally:
        conn.close()
@router.post("/alarm-settings/recipients")
def add_alarm_recipient(data: dict):
    if data.get("admin_password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    email = data.get("email", "").strip()

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    conn = db()
    try:

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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
@router.delete("/alarm-settings/recipients/{recipient_id}")
def delete_alarm_recipient(recipient_id: int, admin_password: str):
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    conn = db()
    try:

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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
@router.put("/alarm-settings/template")
def update_alarm_template(data: dict):
    if data.get("admin_password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    subject_template = data.get("subject_template", "").strip()
    body_template = data.get("body_template", "").strip()

    if not subject_template or not body_template:
        raise HTTPException(status_code=400, detail="Subject and body templates are required")

    conn = db()
    try:

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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
@router.put("/alarm-settings/recipients/{recipient_id}/enabled")
def update_recipient_enabled(recipient_id: int, data: dict):
    if data.get("admin_password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")

    enabled = 1 if data.get("enabled") is True else 0

    conn = db()
    try:

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
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()