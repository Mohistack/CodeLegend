# -*- coding: utf-8 -*-
"""Configuration settings for the codeLegend project scripts."""
import logging
import os

# 配置日志记录
logging.basicConfig(
    level=logging.INFO, # 日志级别
    format='%(asctime)s [codeLegend] %(levelname)s - %(message)s - [%(filename)s][%(lineno)d]', # 日志格式
    handlers=[
        logging.StreamHandler(), # 输出到控制台
        logging.FileHandler( # 输出到文件
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), # 项目根目录
                'codeLegend.log')) # 日志文件名
    ])
logger = logging.getLogger(__name__) # 获取 logger 实例
# --- 基础目录 --- 
# 计算 BASE_DIR 相对于此配置文件位置 (scripts/config.py)
# 上移一级获取 'scripts' 目录，再上移一级获取项目根目录。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 项目根目录
DATA_DIR = os.path.join(BASE_DIR, "public/data") # 数据存储目录
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive") # 归档数据目录

# --- SQLite 数据库 --- 
SQLITE_DB_DIR = os.path.join(BASE_DIR, "db") # SQLite 数据库文件存储目录
USERS_SQLITE_DB_PATH = os.path.join(SQLITE_DB_DIR, "sqlite/users.db") # 用户信息数据库路径
REPOS_SQLITE_DB_PATH = os.path.join(SQLITE_DB_DIR, "sqlite/repos.db") # 仓库信息数据库路径
GITHUB_DB_INFO_PATH = os.path.join(SQLITE_DB_DIR, "sqlite/github_info.db") # GitHub 信息数据库路径
SQLITE_DB_PATHS = [ # 所有 SQLite 数据库路径列表
    USERS_SQLITE_DB_PATH, REPOS_SQLITE_DB_PATH, GITHUB_DB_INFO_PATH
]
DB_DIR = SQLITE_DB_DIR # 数据库目录 (与 SQLITE_DB_DIR 相同)

# --- GitHub API --- 
GITHUB_TOKEN = os.getenv("GH_TOKEN") # 从环境变量获取 GitHub Token

# 确保 GITHUB_TOKEN 已加载
if not GITHUB_TOKEN:
    logger.warning("GITHUB_TOKEN environment variable not set. API requests might fail.") # Token 未设置警告
    # 可选：如果 Token 是必需的，则引发错误或退出
    # raise ValueError("GITHUB_TOKEN environment variable is required.")

HEADERS = { # API 请求头
    "Authorization": f"bearer {GITHUB_TOKEN}", # 认证信息
    "Content-Type": "application/json" # 内容类型
} if GITHUB_TOKEN else { # 如果没有 Token，则不包含 Authorization
    "Content-Type": "application/json"
}

API_BASE_URL = "https://api.github.com" # GitHub API 基础 URL
# 默认请求参数 (可在函数调用中覆盖)
DEFAULT_PER_PAGE = 100 # 每页默认记录数
DEFAULT_PAGES = 2 # 默认请求页数
DEFAULT_TIMEOUT = 60  # 默认请求超时时间 (秒)
USER_DETAILS_TIMEOUT = 30  # 获取用户详情的超时时间 (秒)

# --- API 搜索查询/参数 --- 
# 趋势仓库查询模板，'since' 日期将在代码中格式化
TRENDING_REPO_QUERY_TEMPLATE = "created:>{since}" # 趋势仓库查询模板
TOP_REPO_QUERY = "stars:>1" # 热门仓库查询条件 (Star 数大于 1)
TOP_USER_QUERY = "followers:>1000" # 热门用户查询条件 (粉丝数大于 1000)
REPO_SORT_STARS = "stars" # 仓库排序字段：Star 数
USER_SORT_FOLLOWERS = "followers" # 用户排序字段：粉丝数
ORDER_DESC = "desc" # 排序顺序：降序

# --- 数据抓取时间范围 (天) --- 
DAILY_TIMEFRAME_DAYS = 1 # 每日时间范围
WEEKLY_TIMEFRAME_DAYS = 7 # 每周时间范围
MONTHLY_TIMEFRAME_DAYS = 30 # 每月时间范围

# --- 输出文件名 --- 
DAILY_TRENDING_FILENAME = "daily_trending.json" # 每日趋势仓库文件名
WEEKLY_TRENDING_FILENAME = "weekly_trending.json" # 每周趋势仓库文件名
MONTHLY_TRENDING_FILENAME = "monthly_trending.json" # 每月趋势仓库文件名
ORI_TOP_REPOS_FILENAME = "original_top_repos.json" # 原始热门仓库数据文件名
TOP_REPOS_FILENAME = "top_repos_list.json" # 处理后的热门仓库列表文件名
ORI_TOP_USERS_FILENAME = "original_top_users_list.json" # 原始热门用户数据文件名
TOP_USERS_FILENAME = "top_users_list.json" # 处理后的热门用户列表文件名
ARCHIVE_INDEX_FILENAME = "archive_index.json" # 归档索引文件名
UPDATE_TIME_FILENAME = "update_time.txt" # 更新时间记录文件名



# --- 数据库 --- 

# 从 GitHub API 获取数据 | GitHub API 限制为 1000 条
DEFAULT_QUERY_LIMIT = 1000 # 默认查询限制
MAX_USERS = 50 # 最大用户数
MAX_REPOS = 500 # 最大仓库数 (-1 表示无限制)
USER_TOP_REPOSITORIES_COUNT = 10 # 每个用户获取其 Top 仓库的数量
REPOS_ONE_TIME = 100 # 每次请求获取的仓库数量 (`first` 参数限制为 100)
USERS_ONE_TIME = 25 # 每次请求获取的用户数量

WAIT_TIME_PER_REQUEST = 5 # 请求之间的等待时间 (秒)

# --- GitHub API 速率限制 --- 
# "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"
# 认证请求的速率限制为每小时 5000 次
# Git 事件的速率限制为每小时 1000 次
# GraphQL API 的速率限制为每小时 100 次
# REST API 的速率限制为每小时 100 次

# --- 生成 JSON 文件 --- 
TOP_REPOS_LIMIT = -1 # 热门仓库数量限制 (-1 表示全部)
TOP_USERS_LIMIT = 1000 # 热门用户数量限制
TRENDING_REPO_LIMIT = 500 # 趋势仓库数量限制

# ARCHIVE_INDEX_FILENAME 在上面已定义
ARCHIVE_FILES = [ # 需要归档的文件列表
    DAILY_TRENDING_FILENAME, WEEKLY_TRENDING_FILENAME,
    MONTHLY_TRENDING_FILENAME, TOP_REPOS_FILENAME, TOP_USERS_FILENAME,
    ORI_TOP_REPOS_FILENAME, ORI_TOP_USERS_FILENAME, UPDATE_TIME_FILENAME
]
