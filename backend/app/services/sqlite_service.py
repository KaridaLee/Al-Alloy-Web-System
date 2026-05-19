import json
from sqlalchemy import text
from app.core.database import engine

SYSTEM_TABLE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS sys_sheet_meta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet_name TEXT NOT NULL UNIQUE,
        table_name TEXT NOT NULL,
        columns_json TEXT NOT NULL,
        key_columns_json TEXT,
        header_info_json TEXT,
        last_sync_time TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sys_row_fingerprint (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet_name TEXT NOT NULL,
        row_key TEXT NOT NULL,
        row_hash TEXT NOT NULL,
        updated_at TEXT,
        UNIQUE(sheet_name, row_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sys_sync_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        sync_time TEXT,
        added_count INTEGER DEFAULT 0,
        updated_count INTEGER DEFAULT 0,
        deleted_count INTEGER DEFAULT 0,
        status TEXT,
        detail_json TEXT
    )
    """
]


def init_system_tables():
    with engine.begin() as conn:
        for sql in SYSTEM_TABLE_SQL:
            conn.execute(text(sql))


def upsert_sheet_meta(conn, sheet_name, table_name, columns, key_columns, header_info, last_sync_time):
    conn.execute(text("""
        INSERT INTO sys_sheet_meta(
            sheet_name, table_name, columns_json, key_columns_json, header_info_json, last_sync_time
        )
        VALUES (
            :sheet_name, :table_name, :columns_json, :key_columns_json, :header_info_json, :last_sync_time
        )
        ON CONFLICT(sheet_name) DO UPDATE SET
            table_name=excluded.table_name,
            columns_json=excluded.columns_json,
            key_columns_json=excluded.key_columns_json,
            header_info_json=excluded.header_info_json,
            last_sync_time=excluded.last_sync_time
    """), {
        "sheet_name": sheet_name,
        "table_name": table_name,
        "columns_json": json.dumps(columns, ensure_ascii=False),
        "key_columns_json": json.dumps(key_columns, ensure_ascii=False),
        "header_info_json": json.dumps(header_info, ensure_ascii=False),
        "last_sync_time": last_sync_time
    })


def create_business_table_if_not_exists(conn, table_name, columns):
    defs = [
        '"__row_key" TEXT PRIMARY KEY',
        '"__raw_row_key" TEXT',
        '"__source_file" TEXT',
        '"__source_sheet" TEXT'
    ]
    for col in columns:
        if col in ["__row_key", "__raw_row_key", "__source_file", "__source_sheet"]:
            continue
        defs.append(f'"{col}" TEXT')
    sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(defs)})'
    conn.execute(text(sql))


def add_missing_columns(conn, table_name, columns):
    existing = conn.execute(text(f'PRAGMA table_info("{table_name}")')).mappings().all()
    existing_cols = {x["name"] for x in existing}

    builtin_cols = ["__row_key", "__raw_row_key", "__source_file", "__source_sheet"]
    for col in builtin_cols + columns:
        if col not in existing_cols:
            conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" TEXT'))


def create_search_indexes(conn, table_name, columns):
    target_cols = ["炉号", "牌号", "批次号", "检测时间时间", "检测时间", "判定", "__source_file"]
    all_cols = set(columns) | {"__source_file"}

    for col in target_cols:
        if col in all_cols:
            idx_name = f'idx_{table_name}_{col}'.replace("-", "_")
            conn.execute(text(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table_name}"("{col}")'))


def fetch_all_row_keys(conn, sheet_name):
    rows = conn.execute(text("""
        SELECT row_key, row_hash
        FROM sys_row_fingerprint
        WHERE sheet_name = :sheet_name
    """), {"sheet_name": sheet_name}).mappings().all()
    return {r["row_key"]: r["row_hash"] for r in rows}


def upsert_row_fingerprint(conn, sheet_name, row_key, row_hash, updated_at):
    conn.execute(text("""
        INSERT INTO sys_row_fingerprint(sheet_name, row_key, row_hash, updated_at)
        VALUES (:sheet_name, :row_key, :row_hash, :updated_at)
        ON CONFLICT(sheet_name, row_key) DO UPDATE SET
            row_hash=excluded.row_hash,
            updated_at=excluded.updated_at
    """), {
        "sheet_name": sheet_name,
        "row_key": row_key,
        "row_hash": row_hash,
        "updated_at": updated_at
    })


def delete_row_fingerprint(conn, sheet_name, row_key):
    conn.execute(text("""
        DELETE FROM sys_row_fingerprint
        WHERE sheet_name=:sheet_name AND row_key=:row_key
    """), {
        "sheet_name": sheet_name,
        "row_key": row_key
    })


def upsert_business_row(conn, table_name, row_data):
    cols = list(row_data.keys())
    quoted_cols = [f'"{c}"' for c in cols]

    param_map = {}
    placeholders = []
    update_cols = []

    for i, col in enumerate(cols):
        param_name = f"p_{i}"
        param_map[param_name] = row_data[col]
        placeholders.append(f":{param_name}")

        if col != "__row_key":
            update_cols.append(f'"{col}" = excluded."{col}"')

    sql = f'''
    INSERT INTO "{table_name}" ({", ".join(quoted_cols)})
    VALUES ({", ".join(placeholders)})
    ON CONFLICT("__row_key") DO UPDATE SET
    {", ".join(update_cols)}
    '''

    conn.execute(text(sql), param_map)


def delete_business_row(conn, table_name, row_key):
    conn.execute(text(
        f'DELETE FROM "{table_name}" WHERE "__row_key"=:row_key'
    ), {"row_key": row_key})


def insert_sync_log(file_path, sync_time, added_count, updated_count, deleted_count, status, detail_json):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sys_sync_log(file_path, sync_time, added_count, updated_count, deleted_count, status, detail_json)
            VALUES (:file_path, :sync_time, :added_count, :updated_count, :deleted_count, :status, :detail_json)
        """), {
            "file_path": file_path,
            "sync_time": sync_time,
            "added_count": added_count,
            "updated_count": updated_count,
            "deleted_count": deleted_count,
            "status": status,
            "detail_json": detail_json
        })