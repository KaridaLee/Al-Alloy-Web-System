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
# 企标控制范围管理、保存与 PDF 预览专属路由
# ==========================================

@router.get("/standards/pdfs")
def list_standard_pdfs():
    """直接读取 data/standards 目录下的所有 PDF 文件"""
    from app.core.config import BASE_DIR
    pdf_dir = BASE_DIR / "data" / "standards"
    if not pdf_dir.exists():
        return {"items": []}
    
    pdfs = []
    for p in pdf_dir.glob("*.pdf"):
        pdfs.append({"filename": p.name})
    return {"items": pdfs}


@router.get("/standards/pdfs/{filename}")
def get_standard_pdf_file(filename: str):
    """直接响应 PDF 文件流用于前端 iframe 预览"""
    from app.core.config import BASE_DIR
    from fastapi.responses import FileResponse
    file_path = BASE_DIR / "data" / "standards" / filename
    if file_path.exists():
        return FileResponse(str(file_path), media_type="application/pdf")
    return {"success": False, "message": "PDF文件不存在"}


@router.get("/standards")
def search_standards(brand_name: str = Query("")):
    """
    智能获取牌号列表：
    从实际的 sys_sheet_meta (生产台账数据) 和 enterprise_standard 中汇集所有已知牌号。
    保证哪怕没有手动添加过的牌号，只要在台账里出现过，也能点出来进行填报。
    """
    brands = set()
    
    # 1. 扫描所有的台账表获取真实牌号
    with engine.begin() as conn:
        metas = conn.execute(text("SELECT table_name, columns_json FROM sys_sheet_meta")).mappings().all()
        for m in metas:
            cols = json.loads(m["columns_json"])
            if "牌号" in cols:
                table_name = m["table_name"]
                rows = conn.execute(text(f'SELECT DISTINCT "牌号" FROM "{table_name}" WHERE "牌号" IS NOT NULL AND TRIM("牌号") != \'\'')).fetchall()
                for r in rows:
                    if r[0]: brands.add(str(r[0]).strip())
                    
    # 2. 合并已有标准的牌号
    from app.core.config import DATA_DIR
    db_path = DATA_DIR / "sqlite" / "standards.db"
    if db_path.exists():
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute('SELECT brand_name FROM enterprise_standard')
            for r in cursor.fetchall():
                if r[0]: brands.add(str(r[0]).strip())
                
    # 3. 过滤与排序
    query = brand_name.strip().lower()
    if query:
        brands = {b for b in brands if query in b.lower()}
        
    return {"items": [{"brand_name": b} for b in sorted(list(brands))]}


@router.get("/standards/detail")
def get_standard_detail(brand_name: str = Query(...)):
    """提取单个牌号已保存的标准数据"""
    from app.core.config import DATA_DIR
    db_path = DATA_DIR / "sqlite" / "standards.db"
    if not db_path.exists():
        return {"success": True, "standard": {"tech_req": {}}}

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('SELECT tech_req_json FROM enterprise_standard WHERE brand_name = ?', (brand_name,)).fetchone()

        if not row:
            return {"success": True, "standard": {"tech_req": {}}}

        res = dict(row)
        try:
            # 兼容新版的结构化存储，我们将完整的 {min/max} 结构存放在了 tech_req_json 中
            res["tech_req"] = json.loads(res["tech_req_json"]) if res.get("tech_req_json") else {}
        except Exception:
            res["tech_req"] = {}

        return {"success": True, "standard": res}


class SaveElementItem(BaseModel):
    tech_min: str = ""
    ctrl_min: str = ""
    ctrl_max: str = ""
    tech_max: str = ""

class SaveStandardReq(BaseModel):
    brand_name: str
    elements: dict[str, SaveElementItem]

@router.post("/standards/save")
def save_standard_detail(req: SaveStandardReq):
    """保存前端五宫格填报的结构化数据"""
    from app.core.config import DATA_DIR
    from datetime import datetime
    
    db_path = DATA_DIR / "sqlite" / "standards.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS enterprise_standard (
                brand_name TEXT PRIMARY KEY,
                tech_req_json TEXT,
                ctrl_req_json TEXT,
                updated_at TEXT
            )
        """)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 将传入的结构化数据直接 JSON 序列化并存入 tech_req_json 字段
        tech_json = json.dumps({k: v.dict() for k, v in req.elements.items()}, ensure_ascii=False)
        
        conn.execute("""
            INSERT INTO enterprise_standard (brand_name, tech_req_json, ctrl_req_json, updated_at)
            VALUES (?, ?, '', ?)
            ON CONFLICT(brand_name) DO UPDATE SET
                tech_req_json = excluded.tech_req_json,
                updated_at = excluded.updated_at
        """, (req.brand_name, tech_json, now))
        
    return {"success": True, "message": "保存成功"}