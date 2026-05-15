import json
from fastapi import APIRouter, Query
from sqlalchemy import text
from app.core.database import engine
from app.api.search import ELEMENTS_ORDER  # 复用搜索模块定义的元素列表

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

            # 统计炉数
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

            # 统计牌号分布
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
    要求：批次号必须带有 'DZ' 关键字。
    """
    limit = 10
    all_data = []

    with engine.begin() as conn:
        metas = conn.execute(text("SELECT table_name, columns_json FROM sys_sheet_meta")).mappings().all()
        
        for m in metas:
            cols = json.loads(m["columns_json"])
            # 只有当表包含 牌号、炉号、批次号 时才参与计算
            if "牌号" not in cols or "炉号" not in cols or "批次号" not in cols:
                continue
            
            # 动态确定时间排序列
            time_col = "__row_key"
            if "检测时间时间" in cols: 
                time_col = "检测时间时间"
            elif "检测时间" in cols: 
                time_col = "检测时间"

            # 选取该牌号且批次号包含 'DZ' 的数据
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

    # 1. 对来自不同表的所有符合条件的数据进行全局排序（按检测时间/主键）
    all_data.sort(
        key=lambda x: x.get("检测时间时间") or x.get("检测时间") or x.get("__row_key") or "", 
        reverse=True
    )
    
    # 2. 取全局最近的10条
    recent_10 = all_data[:limit]
    # 3. 折线图从左往右展示，因此需要反转为正序（旧 -> 新）
    recent_10.reverse()

    # 提取炉号作为 X 轴标签
    furnace_nos = [r.get("炉号") or "-" for r in recent_10]
    
    # 提取各元素趋势数据
    trends = {}
    valid_elements = []
    
    for el in ELEMENTS_ORDER:
        vals = []
        has_value = False
        for r in recent_10:
            v = r.get(el)
            # 尝试转换为浮点数，转换失败或为空则补 0
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
        # 只有在最近10条中有实际数据的元素才加入轮播列表，避免轮播全零的空表
        if has_value:
            valid_elements.append(el)

    return {
        "brand": brand,
        "furnace_nos": furnace_nos,
        "trends": trends,
        "elements": valid_elements if valid_elements else ["Al"] # 兜底至少显示 Al
    }