from fastapi import APIRouter, Query
from sqlalchemy import text
from app.core.database import engine
from io import BytesIO
from typing import List
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import openpyxl
import sqlite3
import json

router = APIRouter(prefix="/api/search", tags=["search"])

ELEMENTS_ORDER = [
    "Al", "Si", "Cu", "Mg", "Mn", "Ti", "Fe", "Zn", "Ni", "Pb", "Sn",
    "Sr", "Zr", "Cr", "Ca", "Sb", "Cd", "As", "B", "Be", "Bi", "Co",
    "Ga", "Hg", "Li", "Mo", "Na", "P", "V"
]
ELEMENTS_SET = set(ELEMENTS_ORDER)


class ExportItem(BaseModel):
    row_key: str
    sheet_name: str


class ExportRequest(BaseModel):
    items: List[ExportItem]


def normalize_detail_item(item: dict):
    if not item:
        return item

    base_fields_order = [
        "序号", "炉号", "牌号", "批次号", "班组_班长",
        "针孔度判定", "检测时间时间", "检测时间", "判定", "判定人",
        "发货", "备注", "烂泥指数", "低于内控", "高于内控", "低于内控_高于内控",
        "__source_file", "__source_sheet"
    ]

    base_info = {}
    chemistry = {}
    others = {}

    for key in base_fields_order:
        if key in item:
            base_info[key] = item.get(key)

    for key, value in item.items():
        if key in base_info:
            continue

        if key in ELEMENTS_SET:
            chemistry[key] = value
            continue

        if key.startswith("化学成分"):
            continue

        if key.startswith("__"):
            continue

        others[key] = value

    ordered_chemistry = {}
    for e in ELEMENTS_ORDER:
        if e in chemistry:
            ordered_chemistry[e] = chemistry[e]

    return {
        "baseInfo": base_info,
        "chemistry": ordered_chemistry,
        "others": others
    }


@router.get("")
def search_records(
    furnace_no: str = Query("", description="炉号"),
    grade_no: str = Query("", description="牌号"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    sheet: str = Query("", description="工作表"),
    page: int = Query(1),
    page_size: int = Query(20)
):
    offset = (page - 1) * page_size

    with engine.begin() as conn:
        metas = conn.execute(text("""
            SELECT sheet_name, table_name, columns_json
            FROM sys_sheet_meta
        """)).mappings().all()

        if sheet:
            metas = [m for m in metas if m["sheet_name"] == sheet]

        all_results = []

        for m in metas:
            table_name = m["table_name"]

            pragma_cols = conn.execute(text(f'PRAGMA table_info("{table_name}")')).mappings().all()
            cols = [c["name"] for c in pragma_cols]

            where_clauses = []
            params = {}

            if furnace_no.strip() and "炉号" in cols:
                where_clauses.append('"炉号" LIKE :furnace_no')
                params["furnace_no"] = f"%{furnace_no.strip()}%"

            if grade_no.strip() and "牌号" in cols:
                where_clauses.append('"牌号" LIKE :grade_no')
                params["grade_no"] = f"%{grade_no.strip()}%"

            time_col = None
            if "检测时间时间" in cols:
                time_col = "检测时间时间"
            elif "检测时间" in cols:
                time_col = "检测时间"

            if start_time.strip() and time_col:
                where_clauses.append(f'"{time_col}" >= :start_time')
                params["start_time"] = start_time.strip()

            if end_time.strip() and time_col:
                where_clauses.append(f'"{time_col}" <= :end_time')
                params["end_time"] = end_time.strip()

            if not where_clauses:
                continue

            where_sql = " AND ".join(where_clauses)

            sql = f'''
            SELECT "__row_key", "__source_file", "__source_sheet", *
            FROM "{table_name}"
            WHERE {where_sql}
            ORDER BY "{time_col or '__row_key'}" DESC
            '''
            rows = conn.execute(text(sql), params).mappings().all()

            for r in rows:
                row = dict(r)
                row["_sheet_name"] = m["sheet_name"]
                all_results.append(row)

        total = len(all_results)
        paged = all_results[offset: offset + page_size]

        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "items": paged
        }


@router.get("/detail")
def record_detail(sheet: str, row_key: str):
    with engine.begin() as conn:
        meta = conn.execute(text("""
            SELECT table_name FROM sys_sheet_meta WHERE sheet_name=:sheet
        """), {"sheet": sheet}).mappings().first()

        if not meta:
            return {"success": False, "message": "sheet不存在"}

        row = conn.execute(text(f'''
            SELECT * FROM "{meta["table_name"]}" WHERE "__row_key"=:row_key
        '''), {"row_key": row_key}).mappings().first()

        normalized = normalize_detail_item(dict(row)) if row else None

        return {
            "success": True,
            "item": normalized
        }


@router.post("/export")
def export_excel(req: ExportRequest):
    wb = openpyxl.Workbook()
    ws = wb.worksheets[0]
    ws.title = "Sheet1"

    headers = ["炉号", "牌号", "批次号", "检测时间时间"] + ELEMENTS_ORDER + ["SF"]
    ws.append(headers)

    with engine.begin() as conn:
        for item in req.items:
            meta = conn.execute(
                text("SELECT table_name FROM sys_sheet_meta WHERE sheet_name=:sheet"),
                {"sheet": item.sheet_name}
            ).mappings().first()

            if not meta:
                continue

            table_name = meta["table_name"]
            row_data = conn.execute(
                text(f'SELECT * FROM "{table_name}" WHERE "__row_key"=:rk'),
                {"rk": item.row_key}
            ).mappings().first()

            if row_data:
                row_list = []
                row_list.append(row_data.get("炉号") or "")
                row_list.append(row_data.get("牌号") or "")
                row_list.append(row_data.get("批次号") or "")
                row_list.append(row_data.get("检测时间时间") or row_data.get("检测时间") or "")

                for el in ELEMENTS_ORDER:
                    val = row_data.get(el)
                    if val is None or val == "":
                        row_list.append(0.0)
                    else:
                        try:
                            row_list.append(float(val))
                        except (ValueError, TypeError):
                            row_list.append(val)

                sf_val = row_data.get("SF")
                if sf_val is None or sf_val == "":
                    row_list.append(0.0)
                else:
                    try:
                        row_list.append(float(sf_val))
                    except (ValueError, TypeError):
                        row_list.append(sf_val)

                ws.append(row_list)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=elements_export.xlsx"}
    )


# ==========================================
# 企标控制范围管理专属路由（已彻底精简）
# ==========================================

@router.get("/standards")
def search_standards(brand_name: str = Query("")):
    """模糊查询受控企标列表"""
    from app.core.config import DATA_DIR
    db_path = DATA_DIR / "sqlite" / "standards.db"
    if not db_path.exists():
        return {"items": []}

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        if brand_name.strip():
            cursor = conn.execute(
                'SELECT brand_name, updated_at FROM enterprise_standard WHERE brand_name LIKE ? ORDER BY brand_name ASC',
                (f"%{brand_name.strip()}%",)
            )
        else:
            cursor = conn.execute('SELECT brand_name, updated_at FROM enterprise_standard ORDER BY brand_name ASC')
        rows = cursor.fetchall()
        return {"items": [dict(r) for r in rows]}


@router.get("/standards/detail")
def get_standard_detail(brand_name: str = Query(...)):
    """提取单个牌号的技术与内控范围 JSON"""
    from app.core.config import DATA_DIR
    db_path = DATA_DIR / "sqlite" / "standards.db"
    if not db_path.exists():
        return {"success": False, "message": "标准规程库文件不存在"}

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            'SELECT brand_name, tech_req_json, ctrl_req_json, updated_at FROM enterprise_standard WHERE brand_name = ?',
            (brand_name,)
        ).fetchone()

        if not row:
            return {"success": False, "message": "未检索到对应的规格成分指标要求"}

        res = dict(row)
        try:
            res["tech_req"] = json.loads(res["tech_req_json"]) if res.get("tech_req_json") else {}
            res["ctrl_req"] = json.loads(res["ctrl_req_json"]) if res.get("ctrl_req_json") else {}
        except Exception:
            pass

        return {"success": True, "standard": res}