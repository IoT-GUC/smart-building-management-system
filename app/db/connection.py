import sqlite3
import os
import glob
from app.config import settings

def get_db_connection():
    conn = sqlite3.connect(settings.DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def run_migrations():
    conn = get_db_connection()
    
    # Create migrations table if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Get applied migrations
    applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}
    
    # Find all migration files
    migration_dir = os.path.join(os.path.dirname(__file__), "migrations")
    if not os.path.exists(migration_dir):
        return
        
    migration_files = sorted(glob.glob(os.path.join(migration_dir, "*.py")))
    
    for mf in migration_files:
        version = os.path.basename(mf).replace(".py", "")
        if version not in applied and version != "__init__":
            print(f"Applying migration: {version}")
            
            with open(mf, "r", encoding="utf-8") as f:
                script = f.read()
            
            # Execute migration logic
            # In a real app we might import the module and call up(), 
            # but for simple sql we can just extract the SQL or just exec the python script.
            # We'll expect the migration file to define an `up(conn)` function.
            import importlib.util
            spec = importlib.util.spec_from_file_location(version, mf)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            try:
                mod.up(conn)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Migration {version} failed: {e}")
                raise
                
    conn.close()
