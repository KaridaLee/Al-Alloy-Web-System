import json
import sqlite3
import re
import pdfplumber
from pathlib import Path
from app.core.config import SQLITE_DIR

# 专属企业标准数据库路径
STANDARDS_DB_PATH = SQLITE_DIR / "standards.db"

def init_standards_db():
    """初始化标准数据库，使用 JSON 字段保证未来极佳的扩展性"""
    STANDARDS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(STANDARDS_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS enterprise_standard (
                brand_name TEXT PRIMARY KEY,       -- 牌号 (如 CQBA-A380)
                tech_req_json TEXT,                -- 技术要求范围 (JSON)
                ctrl_req_json TEXT,                -- 内控标准范围 (JSON)
                mech_props_json TEXT,              -- 机械性能 (JSON)
                samples_json TEXT,                 -- 样品送检和发货要求 (JSON)
                updated_at TEXT
            )
        """)

def clean_text(text):
    return str(text).replace("\n", "").strip() if text else ""

def sync_pdf_standard(pdf_path: str):
    """解析 PDF 并同步到企业标准数据库"""
    init_standards_db()
    
    brand_name = Path(pdf_path).stem.split("企业标准")[0]  # 例如从 "CQBA-A380企业标准A1" 提取 "CQBA-A380"
    
    tech_req = {}
    ctrl_req = {}
    mech_props = {}
    samples = {
        "发货试样": [],
        "送检试样": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_content = page.extract_text() or ""
            tables = page.extract_tables()
            
            # --- 1. 提取文本中的试样要求 (灵活兼容未来各种试样描述) ---
            # 简单启发式搜索：寻找包含“试样”、“样模”相关的段落
            paragraphs = text_content.split("\n")
            for para in paragraphs:
                if "发货" in para and ("试样" in para or "样模" in para or "光谱" in para):
                    samples["发货试样"].append(para.strip())
                elif "送检" in para and ("试样" in para or "样模" in para or "光谱" in para):
                    samples["送检试样"].append(para.strip())

            # --- 2. 提取表格数据 (化学成分、机械性能) ---
            for table in tables:
                if not table or not table[0]: continue
                headers = [clean_text(h) for h in table[0]]
                
                # 情况A：化学成分表 (判断依据：表头含有Si, Cu等元素)
                if any(el in headers for el in ["Si%", "Cu%", "Si", "Cu", "化学成分"]):
                    # 找到表头中对应的元素列索引
                    element_cols = {i: h.replace("%", "") for i, h in enumerate(headers) if re.match(r'^[A-Z][a-z]?$', h.replace("%", ""))}
                    
                    for row in table[1:]:
                        row_name = clean_text(row[0])
                        if "技术要求" in row_name:
                            for col_idx, el_name in element_cols.items():
                                tech_req[el_name] = clean_text(row[col_idx])
                        elif "内控标准" in row_name:
                            for col_idx, el_name in element_cols.items():
                                ctrl_req[el_name] = clean_text(row[col_idx])
                                
                # 情况B：机械性能表 (判断依据：含有抗拉强度、延伸率等)
                elif any("抗拉强度" in h or "延伸率" in h or "屈服" in h or "硬度" in h for h in headers):
                    # 获取需要提取的性能索引
                    target_props = ["抗拉强度", "延伸率", "屈服强度", "布氏硬度"]
                    prop_cols = {}
                    for i, h in enumerate(headers):
                        for prop in target_props:
                            if prop in h: prop_cols[prop] = i
                            
                    if len(table) > 1:
                        data_row = table[1] # 取第一行数据
                        for prop, col_idx in prop_cols.items():
                            mech_props[prop] = clean_text(data_row[col_idx])

    # 存入专属数据库
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sqlite3.connect(STANDARDS_DB_PATH) as conn:
        conn.execute("""
            INSERT INTO enterprise_standard (brand_name, tech_req_json, ctrl_req_json, mech_props_json, samples_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(brand_name) DO UPDATE SET
                tech_req_json = excluded.tech_req_json,
                ctrl_req_json = excluded.ctrl_req_json,
                mech_props_json = excluded.mech_props_json,
                samples_json = excluded.samples_json,
                updated_at = excluded.updated_at
        """, (
            brand_name,
            json.dumps(tech_req, ensure_ascii=False),
            json.dumps(ctrl_req, ensure_ascii=False),
            json.dumps(mech_props, ensure_ascii=False),
            json.dumps(samples, ensure_ascii=False),
            now
        ))
    print(f"[PDF_PARSER] 成功提取并存入企业标准: {brand_name}")