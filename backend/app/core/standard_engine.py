import json
import sqlite3
from pathlib import Path
from docx import Document
from app.core.config import SQLITE_DIR, BASE_DIR

STANDARDS_DB_PATH = SQLITE_DIR / "standards.db"

def init_standards_db():
    STANDARDS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(STANDARDS_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS enterprise_standard (
                brand_name TEXT PRIMARY KEY,
                tech_req_json TEXT,
                ctrl_req_json TEXT,
                updated_at TEXT
            )
        """)

def clean_text(text):
    if text is None:
        return ""
    # 彻底清洗换行符、回车符和空格，防止 8.0 \n - \n 11.0 断层
    t = str(text).replace("\n", "").replace("\r", "").replace(" ", "").replace("\t", "").strip()
    return "" if t in ["—", "/", "-", "无"] else t

def sync_word_standard(file_path: str):
    init_standards_db()
    
    # 强制格式校验
    if str(file_path).lower().endswith(".doc"):
        raise ValueError("系统不支持旧版二进制 .doc 格式，请用 Word 打开并另存为 .docx 后再提取！")
        
    filename = Path(file_path).stem
    brand_name = filename.split("企业标准")[0].replace("标准", "").replace("企标", "").strip()
    if " " in brand_name:
        brand_name = brand_name.split(" ")[-1]

    tech_req = {}
    ctrl_req = {}

    try:
        doc = Document(file_path)
    except Exception as e:
        raise ValueError(f"Word文件读取失败 (请确保是原生.docx): {str(e)}")

    if not doc.tables:
        raise ValueError("文档中未发现数据表格")

    table = doc.tables[0]
    
    header_row_idx = -1
    element_cols = {} 

    for r_idx, row in enumerate(table.rows):
        row_texts = [clean_text(cell.text) for cell in row.cells]
        
        found_elements = {}
        for c_idx, cell_text in enumerate(row_texts):
            ct = cell_text.upper()
            el_match = None
            for el in ["SI", "CU", "MG", "MN", "FE", "ZN", "NI", "PB", "SN", "TI", "AL", "CR", "SR", "CA", "SB"]:
                if el in ct:
                    el_match = el.capitalize()
                    break
            # OCR 和拼写容错
            if not el_match:
                if "MRN" in ct or "MR1" in ct: el_match = "Mn"
                elif "ZRN" in ct: el_match = "Zn"
                
            if el_match:
                found_elements[c_idx] = el_match

        if len(found_elements) >= 2:
            header_row_idx = r_idx
            element_cols = found_elements
            break

    if header_row_idx == -1:
        raise ValueError("未在表格中检索到含 Si/Cu/Mg 等特征的表头")

    for r_idx in range(header_row_idx + 1, len(table.rows)):
        row = table.rows[r_idx]
        row_texts = [clean_text(cell.text) for cell in row.cells]
        if not row_texts or not row_texts[0]:
            continue

        row_header = row_texts[0]
        if "技术" in row_header or "要求" in row_header:
            for c_idx, el in element_cols.items():
                if c_idx < len(row_texts):
                    val = row_texts[c_idx]
                    if val: tech_req[el] = val
        elif "内控" in row_header or "内部" in row_header:
            for c_idx, el in element_cols.items():
                if c_idx < len(row_texts):
                    val = row_texts[c_idx]
                    if val: ctrl_req[el] = val

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(STANDARDS_DB_PATH) as conn:
        conn.execute("""
            INSERT INTO enterprise_standard (brand_name, tech_req_json, ctrl_req_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(brand_name) DO UPDATE SET
                tech_req_json = excluded.tech_req_json,
                ctrl_req_json = excluded.ctrl_req_json,
                updated_at = excluded.updated_at
        """, (brand_name, json.dumps(tech_req, ensure_ascii=False), json.dumps(ctrl_req, ensure_ascii=False), now))

def sync_all_standards_in_dir():
    init_standards_db()
    word_dir = BASE_DIR / "data" / "word"
    if not word_dir.exists():
        word_dir.mkdir(parents=True, exist_ok=True)

    # 扫描 .docx 格式，同时扫出 .doc 用于报错提示
    all_files = list(word_dir.glob("*.docx")) + list(word_dir.glob("*.doc"))
    if not all_files:
        return {"success": False, "message": "data/word 目录中没有检测到任何文档"}

    success_count = 0
    failed_list = []

    for f_path in all_files:
        try:
            sync_word_standard(str(f_path))
            success_count += 1
        except Exception as e:
            failed_list.append(f"{f_path.name}: {str(e)}")

    return {
        "success": True,
        "total": len(all_files),
        "success_count": success_count,
        "failed_list": failed_list
    }