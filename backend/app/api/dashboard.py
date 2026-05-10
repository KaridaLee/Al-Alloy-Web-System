import json
from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import engine

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview():
    with engine.begin() as conn:
        sheets = conn.execute(text("""
            SELECT sheet_name, table_name, columns_json, last_sync_time
            FROM sys_sheet_meta
            ORDER BY sheet_name
        """)).mappings().all()

        latest_sync = conn.execute(text("""
            SELECT sync_time, added_count, updated_count, deleted_count, status
            FROM sys_sync_log
            ORDER BY id DESC LIMIT 1
        """)).mappings().first()

        total_rows = 0
        sheet_stats = []
        brand_stats = {}
        judge_stats = {}

        for s in sheets:
            table_name = s["table_name"]
            cols = json.loads(s["columns_json"])
            safe_cols = [c.strip() for c in cols]

            if "炉号" in safe_cols:
                row_count = conn.execute(text(f'''
                    SELECT COUNT(DISTINCT "炉号") AS cnt
                    FROM "{table_name}"
                    WHERE "炉号" IS NOT NULL AND TRIM("炉号") <> ''
                ''')).scalar() or 0
            else:
                row_count = conn.execute(text(f'''
                    SELECT COUNT(1) AS cnt FROM "{table_name}"
                ''')).scalar() or 0

            total_rows += row_count

            sheet_stats.append({
                "sheetName": s["sheet_name"],
                "tableName": table_name,
                "rowCount": row_count,
                "lastSyncTime": s["last_sync_time"]
            })

            if "牌号" in safe_cols and "炉号" in safe_cols:
                rows = conn.execute(text(f'''
                    SELECT "牌号" AS name, COUNT(DISTINCT "炉号") AS cnt
                    FROM "{table_name}"
                    WHERE "牌号" IS NOT NULL AND TRIM("牌号") <> ''
                      AND "炉号" IS NOT NULL AND TRIM("炉号") <> ''
                    GROUP BY "牌号"
                ''')).mappings().all()

                for r in rows:
                    brand_stats[r["name"]] = brand_stats.get(r["name"], 0) + r["cnt"]

            elif "牌号" in safe_cols:
                rows = conn.execute(text(f'''
                    SELECT "牌号" AS name, COUNT(1) AS cnt
                    FROM "{table_name}"
                    WHERE "牌号" IS NOT NULL AND TRIM("牌号") <> ''
                    GROUP BY "牌号"
                ''')).mappings().all()

                for r in rows:
                    brand_stats[r["name"]] = brand_stats.get(r["name"], 0) + r["cnt"]

            if "判定" in safe_cols:
                rows = conn.execute(text(f'''
                    SELECT "判定" AS name, COUNT(1) AS cnt
                    FROM "{table_name}"
                    WHERE "判定" IS NOT NULL AND TRIM("判定") <> ''
                    GROUP BY "判定"
                ''')).mappings().all()

                for r in rows:
                    judge_stats[r["name"]] = judge_stats.get(r["name"], 0) + r["cnt"]

        return {
            "sheetCount": len(sheets),
            "totalRows": total_rows,
            "lastSync": dict(latest_sync) if latest_sync else None,
            "sheetStats": sheet_stats,
            "brandStats": [{"name": k, "count": v} for k, v in brand_stats.items()],
            "judgeStats": judge_stats
        }