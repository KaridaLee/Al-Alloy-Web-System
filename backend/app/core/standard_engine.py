import json
import sqlite3
import pdfplumber
import openpyxl
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
    # 移除换行和空格，方便统一比对
    return str(text).replace("\n", "").replace(" ", "").strip()

def extract_elements_from_row(row_texts):
    found_elements = {}
    for c_idx, cell_text in enumerate(row_texts):
        ct = cell_text.upper()
        el_match = None
        for el in ["SI", "CU", "MG", "MN", "FE", "ZN", "NI", "PB", "SN", "TI", "AL", "CR", "SR", "CA", "SB"]:
            if el in ct:
                el_match = el.capitalize()
                break
        if not el_match:
            if "MRN" in ct or "MR1" in ct: el_match = "Mn"
            elif "ZRN" in ct: el_match = "Zn"
            
        if el_match:
            found_elements[c_idx] = el_match
    return found_elements

def sync_pdf_standard(pdf_path: str):
    init_standards_db()
    brand_name = Path(pdf_path).stem.split("企业标准")[0].replace("标准", "").replace("企标", "").strip()
    
    tech_req = {}
    ctrl_req = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        # 【性能优化】只读取 PDF 的第一页！
        page = pdf.pages[0]
        
        # --- 方案A：优先尝试速度极快的标准网格表格提取 ---
        strategies = [
            {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
            {"vertical_strategy": "text", "horizontal_strategy": "text"}
        ]
        
        for strategy in strategies:
            tables = page.extract_tables(table_settings=strategy)
            for table in tables:
                if not table: continue
                
                header_row_idx = -1
                element_cols = {} 
                
                for r_idx, row in enumerate(table):
                    row_texts = [clean_text(cell) for cell in row]
                    found = extract_elements_from_row(row_texts)
                    if len(found) >= 2:
                        header_row_idx = r_idx
                        element_cols = found
                        break
                        
                if header_row_idx != -1:
                    for row in table[header_row_idx+1:]:
                        row_texts = [clean_text(cell) for cell in row]
                        if not row_texts or not row_texts[0]: continue
                        
                        row_header = row_texts[0]
                        if "技术" in row_header or "要求" in row_header:
                            for c_idx, el in element_cols.items():
                                if c_idx < len(row_texts) and row_texts[c_idx]:
                                    if el not in tech_req: tech_req[el] = row_texts[c_idx]
                        elif "内控" in row_header or "内部" in row_header:
                            for c_idx, el in element_cols.items():
                                if c_idx < len(row_texts) and row_texts[c_idx]:
                                    if el not in ctrl_req: ctrl_req[el] = row_texts[c_idx]
            
            # 如果方案A获取到了数据，直接跳出循环
            if tech_req or ctrl_req:
                break

        # --- 方案B：【终极杀器】如果方案A完全失败，启动几何视觉坐标映射算法 ---
        if not tech_req and not ctrl_req:
            print(f"[PDF_PARSER] 常规表格识别失败，启动终极视觉坐标映射算法: {brand_name}")
            
            # 提取全页所有文字块及其绝对坐标 (x0, top, x1, bottom)
            words = page.extract_words()
            
            # 将 Y 坐标相近的文字聚类为同一行 (容差 5 像素)
            lines = []
            words.sort(key=lambda w: w["top"])
            current_line = []
            current_top = None
            
            for w in words:
                if current_top is None:
                    current_top = w["top"]
                    current_line.append(w)
                elif abs(w["top"] - current_top) < 5:
                    current_line.append(w)
                else:
                    current_line.sort(key=lambda x: x["x0"])
                    lines.append(current_line)
                    current_top = w["top"]
                    current_line = [w]
            if current_line:
                current_line.sort(key=lambda x: x["x0"])
                lines.append(current_line)
                
            # 遍历每一行，寻找“元素表头”行
            for i, line in enumerate(lines):
                line_str = " ".join([w["text"] for w in line]).upper()
                
                # 如果这一行出现了元素
                if any(el in line_str for el in ["SI", "CU", "MG", "FE", "ZN"]):
                    headers = []
                    # 记录下每个元素的中心 X 坐标点
                    for w in line:
                        text_clean = clean_text(w["text"]).upper().replace("%", "")
                        el_match = None
                        for el in ["SI", "CU", "MG", "MN", "FE", "ZN", "NI", "PB", "SN", "TI", "AL", "CR", "SR", "CA", "SB"]:
                            if el in text_clean: el_match = el.capitalize(); break
                        if el_match:
                            headers.append({"el": el_match, "x": (w["x0"] + w["x1"])/2 })
                    
                    if len(headers) >= 2:
                        # 往下找 1 到 5 行去寻找对应的数据
                        for j in range(i+1, min(i+6, len(lines))):
                            data_line = lines[j]
                            data_str = " ".join([w["text"] for w in data_line])
                            is_tech = "技术" in data_str or "要求" in data_str
                            is_ctrl = "内控" in data_str or "内部" in data_str
                            
                            if is_tech or is_ctrl:
                                for w in data_line:
                                    # 忽略掉行首的文本标签
                                    if any(k in w["text"] for k in ["技术", "要求", "内控", "内部", "标准"]):
                                        continue
                                    
                                    # 计算当前这个数据值的中心 X 坐标点
                                    wx = (w["x0"] + w["x1"]) / 2
                                    # 寻找和该数据中心点最接近的上方表头
                                    closest_h = min(headers, key=lambda h: abs(h["x"] - wx))
                                    
                                    # 如果数据中心和表头中心在垂直投影上误差小于 40 像素，完美对齐！
                                    if abs(closest_h["x"] - wx) < 40:
                                        val = clean_text(w["text"])
                                        if val and val not in ["-", "/"]:
                                            if is_tech and closest_h["el"] not in tech_req: tech_req[closest_h["el"]] = val
                                            if is_ctrl and closest_h["el"] not in ctrl_req: ctrl_req[closest_h["el"]] = val
                        break # 找到表头并处理后立刻跳出

    save_to_db(brand_name, tech_req, ctrl_req)
    if not tech_req and not ctrl_req:
        raise ValueError("PDF格式异常极高，无边框视觉算法亦未能找到目标成分数据")
        
    print(f"[PDF_PARSER] 解析完成: {brand_name} | 技术要求提取到 {len(tech_req)} 个 | 内控要求提取到 {len(ctrl_req)} 个")


def sync_excel_standard(excel_path: str):
    """手动 Excel 兜底方案"""
    brand_name = Path(excel_path).stem.split("企业标准")[0].replace("标准", "").replace("企标", "").strip()
    tech_req, ctrl_req = {}, {}
    
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    
    # 核心修复点：使用 worksheets[0] 代替 active 消除编辑器警告
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    
    header_row_idx = -1
    element_cols = {}
    
    for r_idx, row in enumerate(rows):
        row_texts = [clean_text(cell) for cell in row]
        found = extract_elements_from_row(row_texts)
        if len(found) >= 2:
            header_row_idx = r_idx
            element_cols = found
            break
            
    if header_row_idx != -1:
        for row in rows[header_row_idx+1:]:
            row_texts = [clean_text(cell) for cell in row]
            if not row_texts or not row_texts[0]: continue
            row_header = row_texts[0]
            if "技术" in row_header or "要求" in row_header:
                for c_idx, el in element_cols.items():
                    if c_idx < len(row_texts) and row_texts[c_idx]:
                        if el not in tech_req: tech_req[el] = row_texts[c_idx]
            elif "内控" in row_header or "内部" in row_header:
                for c_idx, el in element_cols.items():
                    if c_idx < len(row_texts) and row_texts[c_idx]:
                        if el not in ctrl_req: ctrl_req[el] = row_texts[c_idx]

    save_to_db(brand_name, tech_req, ctrl_req)

def save_to_db(brand_name, tech_req, ctrl_req):
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
    standards_dir = BASE_DIR / "data" / "standards"
    if not standards_dir.exists():
        return {"success": False, "message": "标准目录(data/standards)尚未创建"}

    pdf_files = list(standards_dir.glob("*.pdf"))
    xlsx_files = list(standards_dir.glob("*.xlsx"))
    all_files = pdf_files + xlsx_files

    if not all_files:
        return {"success": False, "message": "目录中没有找到可提取的文件"}

    success_count = 0
    failed_list = []

    for f_path in all_files:
        try:
            if f_path.suffix.lower() == '.pdf':
                sync_pdf_standard(str(f_path))
            elif f_path.suffix.lower() == '.xlsx':
                sync_excel_standard(str(f_path))
            success_count += 1
        except Exception as e:
            failed_list.append(f"{f_path.name}: {str(e)}")

    return {
        "success": True,
        "total": len(all_files),
        "success_count": success_count,
        "failed_list": failed_list
    }