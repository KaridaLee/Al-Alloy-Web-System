from fastapi import APIRouter, Query
from sqlalchemy import text
from app.core.database import engine

router = APIRouter(prefix="/api/search", tags=["search"])

ELEMENTS_ORDER = [
    "Al", "Si", "Cu", "Mg", "Mn", "Ti", "Fe", "Zn", "Ni", "Pb", "Sn",
    "Sr", "Zr", "Cr", "Ca", "Sb", "Cd", "As", "B", "Be", "Bi", "Co",
    "Ga", "Hg", "Li", "Mo", "Na", "P", "V"
]
ELEMENTS_SET = set(ELEMENTS_ORDER)


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
    keyword: str = Query(...),
    field: str = Query("all"),
    sheet: str = Query(""),
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

            where_clauses = []
            params = {"kw": f"%{keyword}%"}

            if field == "furnace":
                where_clauses.append('"炉号" LIKE :kw')
            elif field == "grade":
                where_clauses.append('"牌号" LIKE :kw')
            else:
                clauses = []
                pragma_cols = conn.execute(text(f'PRAGMA table_info("{table_name}")')).mappings().all()
                cols = [c["name"] for c in pragma_cols]
                for c in cols:
                    if c == "__row_key":
                        continue
                    clauses.append(f'"{c}" LIKE :kw')
                if clauses:
                    where_clauses.append("(" + " OR ".join(clauses) + ")")

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            sql = f'''
            SELECT "__row_key", "__source_file", "__source_sheet", *
            FROM "{table_name}"
            WHERE {where_sql}
            ORDER BY "__row_key" DESC
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