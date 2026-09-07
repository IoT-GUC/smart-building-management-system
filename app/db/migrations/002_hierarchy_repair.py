def up(conn):
    # 1. Create a default client and site for legacy data migration
    conn.execute("INSERT OR IGNORE INTO clients (id, name) VALUES (1, 'Legacy Client')")
    conn.execute("INSERT OR IGNORE INTO sites (id, client_id, name) VALUES (1, 1, 'Legacy Site')")
    
    # Ensure columns exist in older data mappings
    
    # We will iterate through old floorplans and move them to floors
    try:
        floorplans = conn.execute("SELECT * FROM floorplans").fetchall()
        for fp in floorplans:
            # ensure building exists
            b_name = fp["building"]
            b_id_row = conn.execute("SELECT id FROM buildings WHERE name = ?", (b_name,)).fetchone()
            if not b_id_row:
                cur = conn.execute("INSERT INTO buildings (site_id, name) VALUES (1, ?)", (b_name,))
                b_id = cur.lastrowid
            else:
                b_id = b_id_row["id"]
            
            # Insert floor
            conn.execute("""
                INSERT INTO floors (building_id, name, floor_number, image_path, image_width, image_height, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (b_id, fp["floor"], fp["floor"], fp["image_path"], fp["image_width"], fp["image_height"], fp["created_at"]))
    except Exception as e:
        print("Floorplans migration skipped or failed:", e)

    # 2. Update Rooms Table
    conn.execute("""
        CREATE TABLE rooms_new(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            floor_id INTEGER NOT NULL,
            room_name TEXT NOT NULL,
            polygon_points TEXT NOT NULL,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (floor_id) REFERENCES floors(id)
        )
    """)
    try:
        old_rooms = conn.execute("SELECT * FROM rooms").fetchall()
        for r in old_rooms:
            b_name = r["building"]
            f_name = r["floor"]
            # Find floor_id
            f_row = conn.execute("""
                SELECT floors.id FROM floors
                JOIN buildings ON buildings.id = floors.building_id
                WHERE buildings.name = ? AND floors.name = ?
            """, (b_name, f_name)).fetchone()
            
            if f_row:
                f_id = f_row["id"]
            else:
                # Create missing hierarchy
                b_id_row = conn.execute("SELECT id FROM buildings WHERE name = ?", (b_name,)).fetchone()
                if not b_id_row:
                    cur = conn.execute("INSERT INTO buildings (site_id, name) VALUES (1, ?)", (b_name,))
                    b_id = cur.lastrowid
                else:
                    b_id = b_id_row["id"]
                    
                cur = conn.execute("INSERT INTO floors (building_id, name, floor_number) VALUES (?, ?, ?)", (b_id, f_name, f_name))
                f_id = cur.lastrowid
                
            conn.execute("""
                INSERT INTO rooms_new (id, floor_id, room_name, polygon_points, x, y, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (r["id"], f_id, r["room_name"], r["polygon_points"], r["x"], r["y"], r["created_at"]))
    except Exception as e:
        print("Rooms data migration skipped or failed:", e)

    conn.execute("DROP TABLE rooms")
    conn.execute("ALTER TABLE rooms_new RENAME TO rooms")
    
    # 3. Update Devices Table
    conn.execute("""
        CREATE TABLE devices_new(
            chip_mac TEXT PRIMARY KEY,
            device_id TEXT,
            dev_eui TEXT,
            join_eui TEXT,
            app_key TEXT,
            node_type TEXT,
            room_id INTEGER,
            label TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    """)
    
    try:
        old_devices = conn.execute("SELECT * FROM devices").fetchall()
        for d in old_devices:
            room_id = None
            if d.get("building") and d.get("floor") and d.get("room"):
                r_row = conn.execute("""
                    SELECT rooms.id FROM rooms
                    JOIN floors ON floors.id = rooms.floor_id
                    JOIN buildings ON buildings.id = floors.building_id
                    WHERE buildings.name = ? AND floors.name = ? AND rooms.room_name = ?
                """, (d["building"], d["floor"], d["room"])).fetchone()
                if r_row:
                    room_id = r_row["id"]
                else:
                    # auto-create for legacy devices
                    b_id_row = conn.execute("SELECT id FROM buildings WHERE name = ?", (d["building"],)).fetchone()
                    if not b_id_row:
                        cur = conn.execute("INSERT INTO buildings (site_id, name) VALUES (1, ?)", (d["building"],))
                        b_id = cur.lastrowid
                    else:
                        b_id = b_id_row["id"]
                        
                    f_row = conn.execute("SELECT id FROM floors WHERE building_id = ? AND name = ?", (b_id, d["floor"])).fetchone()
                    if not f_row:
                        cur = conn.execute("INSERT INTO floors (building_id, name, floor_number) VALUES (?, ?, ?)", (b_id, d["floor"], d["floor"]))
                        f_id = cur.lastrowid
                    else:
                        f_id = f_row["id"]
                        
                    cur = conn.execute("INSERT INTO rooms (floor_id, room_name, polygon_points, x, y) VALUES (?, ?, '[]', 0, 0)", (f_id, d["room"]))
                    room_id = cur.lastrowid

            conn.execute("""
                INSERT INTO devices_new (chip_mac, device_id, dev_eui, join_eui, app_key, node_type, room_id, label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (d["chip_mac"], d["device_id"], d["dev_eui"], d["join_eui"], d["app_key"], d["node_type"], room_id, d["label"]))
    except Exception as e:
        print("Devices data migration skipped or failed:", e)
        
    conn.execute("DROP TABLE devices")
    conn.execute("ALTER TABLE devices_new RENAME TO devices")
    
    # 4. Drop floorplans
    conn.execute("DROP TABLE IF EXISTS floorplans")
