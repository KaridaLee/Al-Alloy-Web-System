import json
from sqlalchemy import text

def init_system_tables():
    from app.core.database import engine
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sys_sheet_meta (
                sheet_name TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                columns_json TEXT,
                key_columns_json TEXT,
                header_info_json TEXT,
                last_sync_time TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sys_row_fingerprint (
                global_row_key TEXT PRIMARY KEY,
                sheet_name TEXT,
                row_hash TEXT NOT NULL,
                last_sync_time TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sys_sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                sync_time TEXT,
                added_count INTEGER,
                updated_count INTEGER,
                deleted_count INTEGER,
                status TEXT,
                detail_json TEXT
            )
        """))

def upsert_sheet_meta(conn, sheet_name, table_name, columns, key_columns, header_info, sync_time):
    conn.execute(text("""
        INSERT INTO sys_sheet_meta 
        (sheet_name, table_name, columns_json, key_columns_json, header_info_json, last_sync_time)
        VALUES (:sn, :tn, :cj, :kcj, :hij, :st)
        ON CONFLICT(sheet_name) DO UPDATE SET
            table_name=excluded.table_name,
            columns_json=excluded.columns_json,
            key_columns_json=excluded.key_columns_json,
            header_info_json=excluded.header_info_json,
            last_sync_time=excluded.last_sync_time
    """), {
        "sn": sheet_name,
        "tn": table_name,
        "cj": json.dumps(columns, ensure_ascii=False),
        "kcj": json.dumps(key_columns, ensure_ascii=False),
        "hij": json.dumps(header_info, ensure_ascii=False),
        "st": sync_time
    })

def create_business_table_if_not_exists(conn, table_name: str, columns: list):
    col_defs = [f'"{col}" TEXT' for col in columns]
    cols_sql = ",\n".join(col_defs)
    sql = f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            "__row_key" TEXT PRIMARY KEY,
            "__raw_row_key" TEXT,
            "__source_file" TEXT,
            "__source_sheet" TEXT,
            {cols_sql}
        )
    '''
    conn.execute(text(sql))

def add_missing_columns(conn, table_name: str, columns: list):
    pragma_rows = conn.execute(text(f'PRAGMA table_info("{table_name}")')).mappings().all()
    existing_columns = {r["name"] for r in pragma_rows}

    for col in columns:
        if col not in existing_columns:
            conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" TEXT'))

def create_search_indexes(conn, table_name: str, columns: list):
    if "炉号" in columns:
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_luhao ON "{table_name}"("炉号")'))
    if "牌号" in columns:
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_paihao ON "{table_name}"("牌号")'))
    if "检测时间" in columns:
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_time ON "{table_name}"("检测时间")'))
    elif "检测时间时间" in columns:
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_time ON "{table_name}"("检测时间时间")'))

def fetch_all_row_keys(conn, sheet_name: str) -> dict:
    rows = conn.execute(text(
        "SELECT global_row_key, row_hash FROM sys_row_fingerprint WHERE sheet_name = :sn"
    ), {"sn": sheet_name}).mappings().all()
    return {r["global_row_key"]: r["row_hash"] for r in rows}

def upsert_row_fingerprint(conn, sheet_name, global_row_key, row_hash, sync_time):
    conn.execute(text("""
        INSERT INTO sys_row_fingerprint (global_row_key, sheet_name, row_hash, last_sync_time)
        VALUES (:gk, :sn, :rh, :st)
        ON CONFLICT(global_row_key) DO UPDATE SET
            row_hash=excluded.row_hash,
            last_sync_time=excluded.last_sync_time
    """), {
        "gk": global_row_key,
        "sn": sheet_name,
        "rh": row_hash,
        "st": sync_time
    })

def delete_row_fingerprint(conn, sheet_name, global_row_key):
    conn.execute(text(
        "DELETE FROM sys_row_fingerprint WHERE global_row_key = :gk"
    ), {"gk": global_row_key})

def upsert_business_row(conn, table_name, row_data: dict):
    cols = list(row_data.keys())
    col_names_str = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join([f":{i}" for i in range(len(cols))])
    
    updates = ", ".join([f'"{cols[i]}"=EXCLUDED."{cols[i]}"' for i in range(len(cols)) if cols[i] != "__row_key"])
    
    sql = f'''
        INSERT INTO "{table_name}" ({col_names_str})
        VALUES ({placeholders})
        ON CONFLICT("__row_key") DO UPDATE SET {updates}
    '''
    
    params = {str(i): row_data[cols[i]] for i in range(len(cols))}
    conn.execute(text(sql), params)

def delete_business_row(conn, table_name, row_key):
    conn.execute(text(f'DELETE FROM "{table_name}" WHERE "__row_key" = :rk'), {"rk": row_key})

def insert_sync_log(file_path, sync_time, added_count, updated_count, deleted_count, status, detail_json):
    from app.core.database import engine
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sys_sync_log 
            (file_path, sync_time, added_count, updated_count, deleted_count, status, detail_json)
            VALUES (:fp, :st, :ac, :uc, :dc, :status, :dj)
        """), {
            "fp": file_path,
            "st": sync_time,
            "ac": added_count,
            "uc": updated_count,
            "dc": deleted_count,
            "status": status,
            "dj": detail_json
        })