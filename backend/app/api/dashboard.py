import json
import re
from fastapi import APIRouter, Query
from sqlalchemy import text
from app.core.database import engine
from app.api.search import ELEMENTS_ORDER, ELEMENTS_SET

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def extract_element_from_col(col_name: str):
    """提取智能清洗后的元素名称，供大屏看板趋势图使用"""
    match = re.match(r'^([A-Z][a-z]?)(?:[^a-zA-Z].*)?$', col_name.strip())
    if match:
        el = match.group(1)
        if el in ELEMENTS_SET:
            return el
    return None

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
    """
    获取指定牌号最近10炉次的元素趋势数据。
    使用提取到的包含 "DZ" 关键字的批次号，同时应用元素表头正则映射。
    """
    limit = 10
    all_data = []

    with engine.begin() as conn:
        metas = conn.execute(text("SELECT table_name, columns_json FROM sys_sheet_meta")).mappings().all()
        
        for m in metas:
            cols = json.loads(m["columns_json"])
            if "牌号" not in cols or "炉号" not in cols or "批次号" not in cols:
                continue
            
            time_col = "__row_key"
            if "检测时间时间" in cols: 
                time_col = "检测时间时间"
            elif "检测时间" in cols: 
                time_col = "检测时间"

            sql = f'''
                SELECT * FROM "{m["table_name"]}" 
                WHERE "牌号" = :brand 
                  AND "批次号" LIKE :batch_filter
                ORDER BY "{time_col}" DESC LIMIT :limit
            '''
            rows = conn.execute(text(sql), {
                "brand": brand, 
                "batch_filter": "%DZ%", 
                "limit": limit
            }).mappings().all()
            
            for r in rows:
                all_data.append(dict(r))

    all_data.sort(
        key=lambda x: x.get("检测时间时间") or x.get("检测时间") or x.get("__row_key") or "", 
        reverse=True
    )
    
    recent_10 = all_data[:limit]
    recent_10.reverse()

    furnace_nos = [r.get("炉号") or "-" for r in recent_10]
    
    trends = {}
    valid_elements = []
    
    for el in ELEMENTS_ORDER:
        vals = []
        has_value = False
        
        for r in recent_10:
            row_dict = dict(r)
            
            # 为当前行动态寻找匹配的实际列名（如 "Si(9.6-12)" -> "Si"）
            actual_col = None
            for k in row_dict.keys():
                if extract_element_from_col(k) == el:
                    actual_col = k
                    break
                    
            v = row_dict.get(actual_col) if actual_col else None
            
            if v is not None and v != "":
                try:
                    num_val = float(v)
                    vals.append(num_val)
                    if num_val > 0: has_value = True
                except:
                    vals.append(0.0)
            else:
                vals.append(0.0)
        
        trends[el] = vals
        if has_value:
            valid_elements.append(el)

    return {
        "brand": brand,
        "furnace_nos": furnace_nos,
        "trends": trends,
        "elements": valid_elements if valid_elements else ["Al"]
    }