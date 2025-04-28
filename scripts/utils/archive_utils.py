import datetime
import json
import os
import shutil

import config

logger = config.logger
# 数据和归档目录路径
# 这些路径需要从主脚本传递或在此处重新定义/计算
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # scripts/utils -> scripts -> GitRank
# DATA_DIR = os.path.join(BASE_DIR, "public/data") # Defined in config
# ARCHIVE_DIR = os.path.join(DATA_DIR, "archive") # Defined in config


def save_json(data, filename):
    """将数据保存为 JSON 文件"""
    try:
        # Convert datetime objects to strings
        def json_serial(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data,
                      f,
                      ensure_ascii=False,
                      indent=2,
                      default=json_serial)
        logger.debug(f"Successfully saved JSON to {filename}")
    except IOError as e:
        logger.error(f"I/O error saving JSON to {filename}: {e}")
        raise # Re-raise IOErrors as they might indicate filesystem issues
    except TypeError as e:
        # Log traceback for serialization errors as they indicate data issues
        logger.error(f"Type error serializing data to JSON for {filename}: {e}", exc_info=True)
        # Decide if you want to raise, or just log and continue
    except Exception as e:
        logger.error(f"Unexpected error saving JSON to {filename}: {e}", exc_info=True)
        # Decide if you want to raise, or just log and continue
    # No finally block needed if we raise on critical errors like IOError


def archive_data():
    """归档当天生成的 JSON 文件并更新索引"""
    logger.info("Archiving generated JSON files...")
    os.makedirs(config.ARCHIVE_DIR, exist_ok=True)
    today = datetime.date.today()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    archive_files_to_move = config.ARCHIVE_FILES

    current_archive_dir = os.path.join(config.ARCHIVE_DIR, year, month, day)
    os.makedirs(current_archive_dir, exist_ok=True)

    for fname in archive_files_to_move:
        src = os.path.join(config.DATA_DIR, fname)
        if os.path.exists(src):
            dst = os.path.join(current_archive_dir, fname)
            try:
                shutil.copy2(src, dst) # Use copy2 to preserve metadata
                logger.info(f"Archived {fname} to {dst}")
            except OSError as e:
                logger.error(f"OS error copying {src} to {dst}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error archiving {fname}: {e}", exc_info=True)
        else:
            logger.warning(
                f"Warning: {fname} not found in {config.DATA_DIR} for archiving."
            )

    # --- Update archive_index.json ---
    logger.info("Updating archive index...")
    index_file_path = os.path.join(config.DATA_DIR,
                                   config.ARCHIVE_INDEX_FILENAME)
    index = {}
    # Load existing index if it exists
    if os.path.exists(index_file_path):
        try:
            with open(index_file_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except json.JSONDecodeError:
            logger.warning(
                f"Warning: Could not decode existing {index_file_path}. Starting fresh index."
            )
        except IOError as e:
            logger.warning(
                f"Warning: Could not read existing {index_file_path}: {e}. Starting fresh index."
            )

    # Walk the archive directory to build/update the index
    for root, dirs, files in os.walk(config.ARCHIVE_DIR):
        # Skip the top-level archive directory itself
        if root == config.ARCHIVE_DIR:
            continue
        for file in files:
            if file.endswith(".json"):
                # Construct relative path from data_dir for web accessibility
                full_file_path = os.path.join(root, file)
                rel_path_from_data = os.path.relpath(full_file_path,
                                                     config.DATA_DIR)
                # Extract date and key from path structure: archive/YYYY/MM/DD/filename.json
                parts = rel_path_from_data.split(os.sep)
                if len(parts) >= 5 and parts[
                        0] == 'archive':  # Ensure correct structure
                    try:
                        y, m, d, fname = parts[1], parts[2], parts[3], parts[4]
                        date_str = f"{y}-{m}-{d}"
                        # Validate date format
                        datetime.datetime.strptime(date_str, '%Y-%m-%d')
                        key = fname.replace(".json", "")
                        if date_str not in index:
                            index[date_str] = {}
                        # Store relative path using forward slashes for web compatibility
                        index[date_str][key] = rel_path_from_data.replace(
                            os.sep, "/")
                    except (ValueError, IndexError) as e:
                        logger.warning(
                            f"Warning: Could not parse date/key from path '{rel_path_from_data}': {e}"
                        )

    # Save the updated index
    save_json(index, index_file_path)
    logger.info(f"Archive index updated and saved to {index_file_path}")


def save_update_time():
    """保存更新时间到文件"""
    update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filepath = os.path.join(config.DATA_DIR, config.UPDATE_TIME_FILENAME)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(update_time)
        logger.info(f"Update time saved to {filepath}")
    except IOError as e:
        logger.error(f"Error saving update time to {filepath}: {e}")


# 读取指定时间的归档的 top_repos.json 文件
def read_archived_top_repos_by_date(date_str: str):
    """读取指定时间的归档的 top_repos.json
    Args:
        date_str (str): 日期字符串，格式为 YYYY-MM-DD
    Returns:
        dict: top_repos.json 的内容
    """
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(
            "Invalid date string format. Expected format is YYYY-MM-DD.")
    # archive_path format: archive/YYYY/MM/DD/top_repos.json
    # convert YYYY-MM-DD to YYYY/MM/DD
    archive_path = os.path.join(config.ARCHIVE_DIR, *date_str.split('-'),
                                config.TOP_REPOS_FILENAME)
    if not os.path.exists(archive_path):
        logger.warning(
            f"Archive file at date {date_str} not found at {archive_path}, skip "
        )
        return None
    with open(archive_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_archived_top_repos_days_before(days: int):
    """读取指定天数前的归档的 top_repos.json
    Args:
        days (int): 要回溯的天数
    Returns:
        dict or None: top_repos.json 的内容，如果找不到则返回 None
    """
    if not isinstance(days, int) or days < 0:
        raise ValueError("Days must be a non-negative integer.")
    target_date = datetime.date.today() - datetime.timedelta(days=days)
    return read_archived_top_repos_by_date(target_date.strftime("%Y-%m-%d"))


def read_archived_top_repos_1d_before_today():
    """读取昨天的归档的 top_repos.json"""
    return read_archived_top_repos_days_before(1)


def read_archived_top_repos_7d_before_today():
    """读取7天前的归档的 top_repos.json"""
    return read_archived_top_repos_days_before(7)


def read_archived_top_repos_30d_before_today():
    """读取30天前的归档的 top_repos.json"""
    return read_archived_top_repos_days_before(30)
