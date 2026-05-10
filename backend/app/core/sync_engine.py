import json
from datetime import datetime
from pathlib import Path

from app.core.database import engine
from app.core.config import SOURCE_DIR
from app.services.excel_reader import parse_workbook, build_row_hash
from app.services.sqlite_service import (
    init_system_tables,
    upsert_sheet_meta,
    create_business_table_if_not_exists,
    add_missing_columns,
    create_search_indexes,
    fetch_all_row_keys,
    upsert_row_fingerprint,
    delete_row_fingerprint,
    upsert_business_row,
    delete_business_row,
    insert_sync_log,
)


def sync_single_excel_to_sqlite(file_path: str):
    print(f"[SYNC] 开始同步单文件: {file_path}")
    parsed_sheets = parse_workbook(file_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_file = Path(file_path).name

    total_added = 0
    total_updated = 0
    total_deleted = 0
    detail = []

    for sheet in parsed_sheets:
        sheet_name = sheet["sheet_name"]
        table_name = sheet["table_name"]
        columns = sheet["columns"]
        key_columns = sheet["key_columns"]
        rows = sheet["rows"]

        header_info = {
            "header_top_row": sheet.get("header_top_row"),
            "header_bottom_row": sheet.get("header_bottom_row"),
            "data_start_row": sheet.get("data_start_row"),
            "effective_max_col": sheet.get("effective_max_col")
        }

        print("-" * 100)
        print(f"[SYNC] 开始处理工作表: {sheet_name}")
        print(f"[SYNC] table_name={table_name}")
        print(f"[SYNC] 列数={len(columns)}, 行数={len(rows)}, key_columns={key_columns}")
        print(f"[SYNC] header_info={header_info}")

        added = 0
        updated = 0
        deleted = 0

        with engine.begin() as conn:
            create_business_table_if_not_exists(conn, table_name, columns)
            add_missing_columns(conn, table_name, columns)
            create_search_indexes(conn, table_name, columns)
            upsert_sheet_meta(conn, sheet_name, table_name, columns, key_columns, header_info, now)

            existing_map = fetch_all_row_keys(conn, sheet_name)
            current_keys = set()

            total_rows = len(rows)

            for idx, row_item in enumerate(rows, start=1):
                raw_row_key = row_item["row_key"]
                row_data = dict(row_item["data"])

                global_row_key = f"{source_file}|{raw_row_key}"

                row_data["__raw_row_key"] = raw_row_key
                row_data["__row_key"] = global_row_key
                row_data["__source_file"] = source_file
                row_data["__source_sheet"] = sheet_name

                row_hash = build_row_hash(row_data)
                current_keys.add(global_row_key)

                old_hash = existing_map.get(global_row_key)

                if old_hash is None:
                    upsert_business_row(conn, table_name, row_data)
                    upsert_row_fingerprint(conn, sheet_name, global_row_key, row_hash, now)
                    added += 1
                elif old_hash != row_hash:
                    upsert_business_row(conn, table_name, row_data)
                    upsert_row_fingerprint(conn, sheet_name, global_row_key, row_hash, now)
                    updated += 1

                if idx % 200 == 0 or idx == total_rows:
                    print(f"[SYNC] {sheet_name}: 已处理 {idx}/{total_rows}")

            # 删除策略：仅删除当前来源文件下、本次不存在的数据
            file_existing_keys = [k for k in existing_map.keys() if k.startswith(f"{source_file}|")]
            for del_idx, row_key in enumerate(file_existing_keys, start=1):
                if row_key not in current_keys:
                    delete_business_row(conn, table_name, row_key)
                    delete_row_fingerprint(conn, sheet_name, row_key)
                    deleted += 1

                if del_idx % 500 == 0 or del_idx == len(file_existing_keys):
                    print(f"[SYNC] {sheet_name}: 删除检查进度 {del_idx}/{len(file_existing_keys)}")

        print(f"[SYNC] 完成工作表: {sheet_name}, added={added}, updated={updated}, deleted={deleted}")

        total_added += added
        total_updated += updated
        total_deleted += deleted

        detail.append({
            "source_file": source_file,
            "sheet_name": sheet_name,
            "table_name": table_name,
            "added": added,
            "updated": updated,
            "deleted": deleted,
            "columns_count": len(columns),
            "row_count": len(rows),
            "key_columns": key_columns,
            "header_info": header_info
        })

    return {
        "success": True,
        "sync_time": now,
        "source_file": source_file,
        "added_count": total_added,
        "updated_count": total_updated,
        "deleted_count": total_deleted,
        "detail": detail
    }


def sync_excel_to_sqlite(file_path: str):
    init_system_tables()
    result = sync_single_excel_to_sqlite(file_path)

    insert_sync_log(
        file_path=file_path,
        sync_time=result["sync_time"],
        added_count=result["added_count"],
        updated_count=result["updated_count"],
        deleted_count=result["deleted_count"],
        status="success",
        detail_json=json.dumps(result["detail"], ensure_ascii=False)
    )

    return result


def sync_all_excels_in_source_dir():
    init_system_tables()

    excel_files = sorted(list(SOURCE_DIR.glob("*.xlsx")))
    if not excel_files:
        return {
            "success": False,
            "message": f"目录 {SOURCE_DIR} 下未找到 .xlsx 文件"
        }

    all_results = []
    total_added = 0
    total_updated = 0
    total_deleted = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for excel_file in excel_files:
        result = sync_single_excel_to_sqlite(str(excel_file))
        all_results.append(result)
        total_added += result["added_count"]
        total_updated += result["updated_count"]
        total_deleted += result["deleted_count"]

    insert_sync_log(
        file_path=str(SOURCE_DIR),
        sync_time=now,
        added_count=total_added,
        updated_count=total_updated,
        deleted_count=total_deleted,
        status="success",
        detail_json=json.dumps(all_results, ensure_ascii=False)
    )

    return {
        "success": True,
        "sync_time": now,
        "file_count": len(excel_files),
        "added_count": total_added,
        "updated_count": total_updated,
        "deleted_count": total_deleted,
        "files": [str(x.name) for x in excel_files],
        "detail": all_results
    }