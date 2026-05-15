import json
from fastapi import APIRouter, Query
from sqlalchemy import text
from app.core.database import engine
from app.api.search import ELEMENTS_ORDER  # 复用元素列表

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

        return {
            "sheetCount": len(sheets),
            "totalRows": total_rows,
            "lastSync": dict(latest_sync) if latest_sync else None,
            "sheetStats": sheet_stats,
            "brandStats": sorted([{"name": k, "count": v} for k, v in brand_stats.items()], key=lambda x: x["count"], reverse=True),
            "judgeStats": judge_stats
        }

@router.get("/brand-trends")
def get_brand_trends(brand: str = Query(..., description="牌号名称")):
    """获取指定牌号最近10炉次的元素趋势"""
    limit = 10
    all_data = []

    with engine.begin() as conn:
        metas = conn.execute(text("SELECT table_name, columns_json FROM sys_sheet_meta")).mappings().all()
        
        for m in metas:
            cols = json.loads(m["columns_json"])
            if "牌号" not in cols or "炉号" not in cols:
                continue
            
            # 找到时间列
            time_col = "__row_key"
            if "检测时间时间" in cols: time_col = "检测时间时间"
            elif "检测时间" in cols: time_col = "检测时间"

            # 选取该牌号在该表中的数据
            sql = f'''
                SELECT * FROM "{m["table_name"]}" 
                WHERE "牌号" = :brand 
                ORDER BY "{time_col}" DESC LIMIT :limit
            '''
            rows = conn.execute(text(sql), {"brand": brand, "limit": limit}).mappings().all()
            for r in rows:
                all_data.append(dict(r))

    # 按时间全局排序取最近10条
    # 假设有检测时间则按时间排，没有则按row_key
    all_data.sort(key=lambda x: x.get("检测时间时间") or x.get("检测时间") or x.get("__row_key") or "", reverse=True)
    recent_10 = all_data[:limit]
    recent_10.reverse() # 转为正序显示

    # 提取炉号
    furnace_nos = [r.get("炉号") or "-" for r in recent_10]
    
    # 提取各元素趋势
    trends = {}
    for el in ELEMENTS_ORDER:
        vals = []
        for r in recent_10:
            v = r.get(el)
            try:
                vals.append(float(v)) if v else vals.append(0.0)
            except:
                vals.append(0.0)
        trends[el] = vals

    return {
        "brand": brand,
        "furnace_nos": furnace_nos,
        "trends": trends,
        "elements": [el for el in ELEMENTS_ORDER if any(trends[el])] # 只返回有数据的元素进行轮播
    }