import hashlib
import json
import openpyxl

def build_row_hash(row_data: dict) -> str:
    """生成单行数据的指纹"""
    filtered_data = {k: v for k, v in row_data.items() if not k.startswith("__")}
    sorted_items = sorted(filtered_data.items(), key=lambda x: x[0])
    row_str = json.dumps(sorted_items, ensure_ascii=False)
    return hashlib.md5(row_str.encode('utf-8')).hexdigest()

def clean_column_name(col_val, col_index) -> str:
    """终极强力清洗：抹除换行、回车、空格和引发SQL崩溃的引号"""
    if col_val is None:
        return f"Unnamed_{col_index}"
    
    # 彻底清除不可见字符和非法引号
    cleaned = str(col_val).replace('\n', '').replace('\r', '').replace(' ', '').replace('"', '').replace("'", "").strip()
    
    if not cleaned:
        return f"Unnamed_{col_index}"
    return cleaned

def parse_single_sheet(file_path: str, sheet_name: str):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb[sheet_name]

    max_row = ws.max_row
    max_col = ws.max_column

    if max_row == 0 or max_col == 0:
        return None

    # 1. 定位表头底部行 (寻找“炉号”或“牌号”)
    header_bottom_row = 1
    found_header = False
    for r in range(1, min(10, max_row + 1)):
        for c in range(1, max_col + 1):
            val = ws.cell(row=r, column=c).value
            if val and isinstance(val, str) and ("炉号" in val or "牌号" in val):
                header_bottom_row = r
                found_header = True
                break
        if found_header:
            break

    # 2. 定位数据范围边界
    min_col = 1
    for c in range(1, max_col + 1):
        if ws.cell(row=header_bottom_row, column=c).value is not None:
            min_col = c
            break

    effective_max_col = max_col
    for c in range(max_col, min_col - 1, -1):
        if ws.cell(row=header_bottom_row, column=c).value is not None:
            effective_max_col = c
            break

    # ==========================================
    # 核心修复点：提取并深度清洗表头，确保列名合法且绝对不重复
    # ==========================================
    headers = []
    seen_headers = set()
    
    for col_idx in range(min_col, effective_max_col + 1):
        val = ws.cell(row=header_bottom_row, column=col_idx).value
        cleaned_col = clean_column_name(val, col_idx)
        
        # 绝对去重逻辑：如果清洗后发现列名重复，自动追加 _1, _2
        final_col = cleaned_col
        counter = 1
        while final_col in seen_headers:
            final_col = f"{cleaned_col}_{counter}"
            counter += 1
            
        seen_headers.add(final_col)
        headers.append(final_col)

    # 3. 提取数据行
    data_start_row = header_bottom_row + 1
    rows_data = []

    for r_idx in range(data_start_row, max_row + 1):
        is_empty_row = True
        row_dict = {}
        for c_idx in range(min_col, effective_max_col + 1):
            val = ws.cell(row=r_idx, column=c_idx).value
            if val is not None and str(val).strip() != "":
                is_empty_row = False
            
            # 使用清洗并去重后的表头作为 key
            header_key = headers[c_idx - min_col]
            row_dict[header_key] = val

        if not is_empty_row:
            rows_data.append({
                "row_key": str(r_idx),
                "data": row_dict
            })

    # 4. 提取主键列
    key_columns = []
    if "炉号" in headers:
        key_columns.append("炉号")
    if "检测时间" in headers:
        key_columns.append("检测时间")
    elif "检测时间时间" in headers:
        key_columns.append("检测时间时间")

    return {
        "sheet_name": sheet_name,
        "table_name": f"tbl_{sheet_name}",
        "columns": headers,
        "key_columns": key_columns,
        "header_top_row": 1,
        "header_bottom_row": header_bottom_row,
        "data_start_row": data_start_row,
        "effective_max_col": effective_max_col,
        "rows": rows_data
    }

def parse_workbook(file_path: str):
    wb = openpyxl.load_workbook(file_path, read_only=True)
    sheet_names = wb.sheetnames
    wb.close()

    result = []
    for sheet_name in sheet_names:
        sheet_data = parse_single_sheet(file_path, sheet_name)
        if sheet_data and len(sheet_data["rows"]) > 0:
            result.append(sheet_data)

    return result