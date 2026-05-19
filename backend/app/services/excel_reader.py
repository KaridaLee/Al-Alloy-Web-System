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
    """终极洗表器：抹除换行、回车、空格和非法引号"""
    if col_val is None:
        return f"Unnamed_{col_index}"
    # 彻底清洗
    cleaned = str(col_val).replace('\n', '').replace('\r', '').replace(' ', '').replace('"', '').replace("'", "").strip()
    if not cleaned:
        return f"Unnamed_{col_index}"
    return cleaned

def parse_single_sheet(file_path: str, sheet_name: str):
    # 【性能优化恢复】：启用 read_only=True，大幅降低内存占用，提升数倍读取速度
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    ws = wb[sheet_name]

    header_bottom_row_idx = -1
    min_col_idx = 0
    effective_max_col_idx = 0
    
    headers = []
    seen_headers = set()
    rows_data = []

    # 【核心性能恢复】：使用 values_only=True 的 C 语言级迭代器，拒绝慢速的 ws.cell()
    row_iterator = ws.iter_rows(values_only=True)
    current_row_idx = 1
    
    # 1. 高速扫描寻找表头
    for row in row_iterator:
        found_header = False
        for val in row:
            if val and isinstance(val, str) and ("炉号" in val or "牌号" in val):
                header_bottom_row_idx = current_row_idx
                found_header = True
                break
        
        if found_header:
            # 确定有效数据列的边界
            first_non_none = 0
            last_non_none = len(row) - 1
            
            for i, v in enumerate(row):
                if v is not None:
                    first_non_none = i
                    break
            for i in range(len(row)-1, -1, -1):
                if row[i] is not None:
                    last_non_none = i
                    break
                    
            min_col_idx = first_non_none
            effective_max_col_idx = last_non_none
            
            # 提取并严格清洗表头，绝对去重
            for i in range(min_col_idx, effective_max_col_idx + 1):
                val = row[i]
                cleaned_col = clean_column_name(val, i + 1)
                
                final_col = cleaned_col
                counter = 1
                while final_col in seen_headers:
                    final_col = f"{cleaned_col}_{counter}"
                    counter += 1
                    
                seen_headers.add(final_col)
                headers.append(final_col)
                
            current_row_idx += 1
            break
        
        current_row_idx += 1

    if header_bottom_row_idx == -1:
        wb.close()
        return None

    # 2. 高速流式提取数据行 (直接顺着迭代器往下读，内存极低)
    for row in row_iterator:
        is_empty_row = True
        row_dict = {}
        
        # 边界安全拦截
        if len(row) <= min_col_idx:
            current_row_idx += 1
            continue
            
        for i in range(min_col_idx, min(effective_max_col_idx + 1, len(row))):
            val = row[i]
            if val is not None and str(val).strip() != "":
                is_empty_row = False
            
            header_key = headers[i - min_col_idx]
            row_dict[header_key] = val

        if not is_empty_row:
            rows_data.append({
                "row_key": str(current_row_idx),
                "data": row_dict
            })
        
        current_row_idx += 1

    wb.close()

    key_columns = []
    if "炉号" in headers: key_columns.append("炉号")
    if "检测时间" in headers: key_columns.append("检测时间")
    elif "检测时间时间" in headers: key_columns.append("检测时间时间")

    return {
        "sheet_name": sheet_name,
        "table_name": f"tbl_{sheet_name}",
        "columns": headers,
        "key_columns": key_columns,
        "header_top_row": 1,
        "header_bottom_row": header_bottom_row_idx,
        "data_start_row": header_bottom_row_idx + 1,
        "effective_max_col": effective_max_col_idx + 1,
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