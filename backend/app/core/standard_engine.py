import json
import sqlite3
import pdfplumber
from pathlib import Path
from app.core.config import SQLITE_DIR, BASE_DIR

# 专属企业标准数据库路径
STANDARDS_DB_PATH = SQLITE_DIR / "standards.db"

def init_standards_db():
    """初始化标准数据库，仅保留成分内控和技术范围"""
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
    if not text:
        return ""
    # 移除换行和所有空格，方便统一匹配
    return str(text).replace("\n", "").replace(" ", "").strip()

def sync_pdf_standard(pdf_path: str):
    """解析 PDF，使用强壮的动态表头锚定算法稳定提取化学成分"""
    init_standards_db()
    
    brand_name = Path(pdf_path).stem.split("企业标准")[0]
    
    tech_req = {}
    ctrl_req = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            
            for table in tables:
                if not table: continue
                
                header_row_idx = -1
                element_cols = {} # 记录：列索引 -> 元素名称
                
                # 1. 动态寻找包含元素的真正表头行
                for r_idx, row in enumerate(table):
                    row_texts = [clean_text(cell) for cell in row]
                    found_elements = {}
                    
                    for c_idx, cell_text in enumerate(row_texts):
                        ct = cell_text.upper()
                        el_match = None
                        
                        # 标准元素列表匹配
                        for el in ["SI", "CU", "MG", "MN", "FE", "ZN", "NI", "PB", "SN", "TI", "AL", "CR", "SR", "CA", "SB"]:
                            if el in ct:
                                el_match = el.capitalize()
                                break
                                
                        # 特殊处理常见的 OCR 识别错误
                        if not el_match:
                            if "MRN" in ct or "MR1" in ct: el_match = "Mn"
                            elif "ZRN" in ct: el_match = "Zn"
                            
                        if el_match:
                            found_elements[c_idx] = el_match
                            
                    # 如果一行里识别到了3个及以上的元素，那这一行绝对是真正的表头
                    if len(found_elements) >= 3:
                        header_row_idx = r_idx
                        element_cols = found_elements
                        break
                        
                # 2. 如果找到了表头，往下寻找对应的数据行
                if header_row_idx != -1:
                    for row in table[header_row_idx+1:]:
                        row_texts = [clean_text(cell) for cell in row]
                        if not row_texts or not row_texts[0]: continue
                        
                        row_header = row_texts[0]
                        # 提取技术要求
                        if "技术" in row_header or "要求" in row_header:
                            for c_idx, el in element_cols.items():
                                if c_idx < len(row_texts) and row_texts[c_idx]:
                                    val = row_texts[c_idx]
                                    if val and el not in tech_req:
                                        tech_req[el] = val
                        # 提取内控标准
                        elif "内控" in row_header or "内部" in row_header:
                            for c_idx, el in element_cols.items():
                                if c_idx < len(row_texts) and row_texts[c_idx]:
                                    val = row_texts[c_idx]
                                    if val and el not in ctrl_req:
                                        ctrl_req[el] = val

    # 存入专属数据库
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
        """, (
            brand_name,
            json.dumps(tech_req, ensure_ascii=False),
            json.dumps(ctrl_req, ensure_ascii=False),
            now
        ))
    print(f"[PDF_PARSER] 解析完成: {brand_name} | 技术要求提取到 {len(tech_req)} 个元素 | 内控要求提取到 {len(ctrl_req)} 个元素")


def sync_all_standards_in_dir():
    """手动触发：扫描企业标准目录下的所有 PDF 并统一提取"""
    standards_dir = BASE_DIR / "data" / "standards"
    if not standards_dir.exists():
        return {"success": False, "message": "标准目录(data/standards)尚未创建或为空"}

    pdf_files = list(standards_dir.glob("*.pdf"))
    if not pdf_files:
        return {"success": False, "message": "目录中没有找到可提取的 .pdf 企业标准文件"}

    success_count = 0
    failed_list = []

    for pdf_path in pdf_files:
        try:
            sync_pdf_standard(str(pdf_path))
            success_count += 1
        except Exception as e:
            failed_list.append(f"{pdf_path.name}: {str(e)}")

    return {
        "success": True,
        "total": len(pdf_files),
        "success_count": success_count,
        "failed_list": failed_list
    }