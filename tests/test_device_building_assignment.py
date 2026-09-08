import pytest
from app.main import create_login_session, create_password_hash

def test_device_building_creation_and_assignment(client, db_conn):
    # 0. Seed admin user & session
    pw_data = create_password_hash("Password123!")
    cursor_admin = db_conn.execute("""
        INSERT INTO users (email, name, role, enabled, password_hash, password_salt)
        VALUES ('admin_bldg_test@test.local', 'Admin Building Test', 'admin', 1, ?, ?)
    """, (pw_data["password_hash"], pw_data["password_salt"]))
    admin_id = cursor_admin.lastrowid
    db_conn.commit()

    admin_token = create_login_session(db_conn, admin_id)
    client.cookies.set("sbms_session", admin_token)

    # 1. Setup client, site, building, floor, room
    c_res = client.post("/clients", json={"name": "Building Test Client"})
    assert c_res.status_code == 200, c_res.text
    client_id = c_res.json()["client_id"]

    s_res = client.post("/sites", json={"client_id": client_id, "name": "Building Test Site"})
    assert s_res.status_code == 200, s_res.text
    site_id = s_res.json()["site_id"]

    b1_res = client.post("/buildings", json={"site_id": site_id, "name": "Alpha Tower"})
    assert b1_res.status_code == 200, b1_res.text
    b1_id = b1_res.json()["building_id"]

    b2_res = client.post("/buildings", json={"site_id": site_id, "name": "Beta Tower"})
    assert b2_res.status_code == 200, b2_res.text
    b2_id = b2_res.json()["building_id"]

    f_res = client.post("/floors", json={"building_id": b1_id, "name": "Floor 1", "floor_number": "1"})
    assert f_res.status_code == 200, f_res.text
    f_id = f_res.json()["floor_id"]

    r_res = client.post(f"/floors/{f_id}/rooms", json={
        "room_name": "Lobby 101",
        "polygon_points": [{"x": 10, "y": 10}, {"x": 50, "y": 10}, {"x": 50, "y": 50}]
    })
    assert r_res.status_code == 200, r_res.text
    r_id = r_res.json()["room_id"]

    # 2. Test POST /devices creating a device assigned to Alpha Tower (b1_id)
    dev1_res = client.post("/devices", json={
        "device_id": "BUILDING-NODE-001",
        "label": "Lobby Sensor",
        "node_type": "environment",
        "building_id": b1_id,
        "floor_id": f_id,
        "room_id": r_id
    })
    assert dev1_res.status_code == 200, dev1_res.text
    assert dev1_res.json()["status"] == "created"
    assert dev1_res.json()["device"]["device_id"] == "BUILDING-NODE-001"
    assert dev1_res.json()["device"]["building_id"] == b1_id

    # 3. Test GET /buildings/{building_id}/devices
    bldg_devs_res = client.get(f"/buildings/{b1_id}/devices")
    assert bldg_devs_res.status_code == 200, bldg_devs_res.text
    devices = bldg_devs_res.json()
    assert any(d["device_id"] == "BUILDING-NODE-001" for d in devices)

    # 4. Test PUT /devices/{device_id}/assign-building to reassign device to Beta Tower (b2_id)
    reassign_res = client.put("/devices/BUILDING-NODE-001/assign-building", json={
        "building_id": b2_id
    })
    assert reassign_res.status_code == 200, reassign_res.text
    assert reassign_res.json()["status"] == "assigned"
    assert reassign_res.json()["device"]["building_id"] == b2_id

    # 5. Verify device moved from b1 to b2
    b1_devs = client.get(f"/buildings/{b1_id}/devices").json()
    assert not any(d["device_id"] == "BUILDING-NODE-001" for d in b1_devs)

    b2_devs = client.get(f"/buildings/{b2_id}/devices").json()
    assert any(d["device_id"] == "BUILDING-NODE-001" for d in b2_devs)

    # 6. Test error validation
    dup_res = client.post("/devices", json={
        "device_id": "BUILDING-NODE-001",
        "building_id": b1_id
    })
    assert dup_res.status_code == 400

    bad_bldg_res = client.post("/devices", json={
        "device_id": "BUILDING-NODE-999",
        "building_id": 999999
    })
    assert bad_bldg_res.status_code == 404
