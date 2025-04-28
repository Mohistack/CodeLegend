# -*- coding: utf-8 -*-
"""Configuration settings for the codeLegend project scripts."""
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [codeLegend] %(levelname)s - %(message)s - [%(filename)s][%(lineno)d]',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'codeLegend.log'))
    ])
logger = logging.getLogger(__name__)
# --- Base Directories ---
# Calculate BASE_DIR relative to this config file's location (scripts/config.py)
# Go up one level to get the 'scripts' directory, then one more to get the project root.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "public/data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")

# sqlite3 DB
SQLITE_DB_DIR = os.path.join(BASE_DIR, "db")
USERS_SQLITE_DB_PATH = os.path.join(SQLITE_DB_DIR, "sqlite/users.db")
REPOS_SQLITE_DB_PATH = os.path.join(SQLITE_DB_DIR, "sqlite/repos.db")
GITHUB_DB_INFO_PATH = os.path.join(SQLITE_DB_DIR, "sqlite/github_info.db")
SQLITE_DB_PATHS = [
    USERS_SQLITE_DB_PATH, REPOS_SQLITE_DB_PATH, GITHUB_DB_INFO_PATH
]
DB_DIR = SQLITE_DB_DIR
# --- GitHub API ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Ensure GITHUB_TOKEN is loaded
if not GITHUB_TOKEN:
    logger.warning("GITHUB_TOKEN environment variable not set. API requests might fail.")
    # Optionally, raise an error or exit if the token is critical
    # raise ValueError("GITHUB_TOKEN environment variable is required.")

HEADERS = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
} if GITHUB_TOKEN else {
    "Content-Type": "application/json"
}

API_BASE_URL = "https://api.github.com"
# Default request parameters (can be overridden in function calls)
DEFAULT_PER_PAGE = 100
DEFAULT_PAGES = 2
DEFAULT_TIMEOUT = 60  # seconds
USER_DETAILS_TIMEOUT = 30  # seconds

# --- API Search Queries/Parameters ---
# Template for trending repos, 'since' date will be formatted in
TRENDING_REPO_QUERY_TEMPLATE = "created:>{since}"
TOP_REPO_QUERY = "stars:>1"
TOP_USER_QUERY = "followers:>1000"
REPO_SORT_STARS = "stars"
USER_SORT_FOLLOWERS = "followers"
ORDER_DESC = "desc"

# --- Data Fetching Timeframes (in days) ---
DAILY_TIMEFRAME_DAYS = 1
WEEKLY_TIMEFRAME_DAYS = 7
MONTHLY_TIMEFRAME_DAYS = 30

# --- Output Filenames ---
DAILY_TRENDING_FILENAME = "daily_trending.json"
WEEKLY_TRENDING_FILENAME = "weekly_trending.json"
MONTHLY_TRENDING_FILENAME = "monthly_trending.json"
ORI_TOP_REPOS_FILENAME = "original_top_repos.json"
TOP_REPOS_FILENAME = "top_repos_list.json"
ORI_TOP_USERS_FILENAME = "original_top_users_list.json"
TOP_USERS_FILENAME = "top_users_list.json"
ARCHIVE_INDEX_FILENAME = "archive_index.json"
UPDATE_TIME_FILENAME = "update_time.txt"



# --- Database ---

# DB_PATH is defined above
DEFAULT_QUERY_LIMIT = 1000
MAX_USERS = 1000
MAX_REPOS = -1 # -1 means no limit
USER_TOP_REPOSITORIES_COUNT = 10
REPOS_ONE_TIME = 100 # `first` limit of 100 records
USERS_ONE_TIME = 25

# --- GitHub API Rate Limiting ---

# Rate limit is 5000 requests per hour for authenticated requests
# Rate limit is 1000 requests per hour for Git events
# Rate limit is 100 requests per hour for GraphQL API
# Rate limit is 100 requests per hour for REST API

# --- Generate JSON Files ---
TOP_REPOS_LIMIT = -1 # -1 means all
TOP_USERS_LIMIT = 1000
TRENDING_REPO_LIMIT = 500

# ARCHIVE_INDEX_FILENAME is defined above
ARCHIVE_FILES = [
    DAILY_TRENDING_FILENAME, WEEKLY_TRENDING_FILENAME,
    MONTHLY_TRENDING_FILENAME, TOP_REPOS_FILENAME, TOP_USERS_FILENAME
]
