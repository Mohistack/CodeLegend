import datetime
from functools import wraps
import os
import time
from typing import Optional, List, Dict


# Import configuration
import config
import requests
from config import logger
from utils.archive_utils import (archive_data,
                                 read_archived_top_repos_1d_before_today,
                                 read_archived_top_repos_7d_before_today,
                                 read_archived_top_repos_30d_before_today,
                                 save_json, save_update_time)
# Import utility functions
from utils.db_utils import (batch_update_accumulated_stars, get_repos_hot,
                            get_repos_hot_order_by_range_day,
                            get_top_followergazer_count_users,
                            get_total_count_by_datetime, save_repositories,
                            save_users, update_total_count, init_db)

# --- Constants ---
# Define a constant for the datetime format string
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

GET_TOP_REPOS_QUERY = """
query getToprepos($queryString: String!, $number_of_repos: Int, $cursor: String){
  search(query:$queryString, type: REPOSITORY, first: $number_of_repos, after: $cursor) {
    repositoryCount
    edges {
			cursor
      node {
        ... on Repository {
					databaseId
					id
          name
          url
					languages (first: 3, orderBy: {field: SIZE,direction: DESC} ) {
						nodes {
							name
						}
					}
          stargazerCount
					description
					createdAt

        }
      }
    }
  }
}
"""

GET_TOP_USERS_QUERY = """
query getTopUsers(
	$queryString: String!
	$number_of_users: Int!
	$usertopRepositories_count: Int!,
	$cursor: String
) {
	search(
		query: $queryString
		type: USER
		first: $number_of_users
		after: $cursor
		
	) {
		userCount
		edges {
			cursor
			node {
				... on User {
					id
					databaseId
					name
					followers {
						totalCount
					}
					login
					url
					avatarUrl
					topRepositories(
						first: $usertopRepositories_count
						orderBy: { field: STARGAZERS, direction: DESC }
					) {
						nodes {
							stargazerCount
						}
					}
				}
			}
		}
	}
}
"""

# --- GitHub API Fetching ---
# 使用github graphQL API to fetch top repos and add retry logic for internet connection errors


def retry_on_network_error(max_retries=3, delay=5, allowed_exceptions=(requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.ChunkedEncodingError,requests.exceptions.HTTPError)):
    """Decorator to retry a function on specific network-related exceptions.
    Parameters:
        max_retries (int): The maximum number of retries.
        delay (int): The delay between retries in seconds.
        allowed_exceptions (tuple): The exceptions to catch and retry.
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    retries += 1
                    last_exception = e
                    wait_time = delay * (2**(retries - 1)) # Exponential backoff
                    logger.warning(
                        f"Network error in {func.__name__} ({type(e).__name__}: {e}). "
                        f"Retrying {retries}/{max_retries} after {wait_time}s..."
                    )
                    time.sleep(wait_time)
                except requests.exceptions.RequestException as e:
                    # Catch other RequestExceptions that weren't specified for retry
                    logger.error(f"Non-retryable network error in {func.__name__}: {type(e).__name__} - {e}")
                    raise # Re-raise immediately
                except Exception as e:
                    # Catch any other unexpected exceptions
                    logger.error(f"Unexpected error in {func.__name__}: {type(e).__name__} - {e}", exc_info=True)
                    raise # Re-raise immediately

            logger.error(
                f"Function {func.__name__} failed after {max_retries} retries.")
            # Raise the last caught retryable exception
            raise ConnectionError(
                f"Failed to execute {func.__name__} after {max_retries} retries. Last error: {type(last_exception).__name__} - {last_exception}"
            ) from last_exception

        return wrapper

    return decorator


@retry_on_network_error(max_retries=3, delay=2)
def fetch_top_users_by_graphql(number_of_users: int = 5,
                               usertopRepositories_count: int = 10,
                               cursor: Optional[str] = None):
    logger.info("Fetching top users using GraphQL...") # Changed print to logger.info
    url = f"{config.API_BASE_URL}/graphql"
    payload = {
        "query": GET_TOP_USERS_QUERY,
        "operationName": "getTopUsers",
        "variables": {
            "queryString": "type:user followers:>0 sort:followers-desc",
            "number_of_users": number_of_users,
            "usertopRepositories_count": usertopRepositories_count,
            "cursor": cursor
        }
    }
    time.sleep(config.WAIT_TIME_PER_REQUEST)
    response = requests.request("POST",
                                url,
                                json=payload,
                                headers=config.HEADERS)
    if response.status_code == 429:
        logger.warning("Too many requests, sleeping for 10 seconds")
        time.sleep(10)
        return fetch_top_users_by_graphql(number_of_users,
                                          usertopRepositories_count, cursor)
    if response.status_code != 200:
        logger.warning(f"{response.status_code}|{response.text}")
    response.raise_for_status()
    return response.json()


# define the function of calling fetch_top_users_by_graphql to fetch all users and save to db


def fetch_all_users_by_graphql(max_number_of_users,
                               number_of_users_one_time=20,
                               usertopRepositories_count=10):
    # how to aggregate the data
    cursor = None  # initialize the cursor
    all_number_of_users_fetched = 0
    users_total_count = 0
    all_users_data = {"meta": {}, "top_users": []}
    while all_number_of_users_fetched < max_number_of_users:
        users_data_info = fetch_top_users_by_graphql(number_of_users_one_time,
                                                     usertopRepositories_count,
                                                     cursor)
        users_data_fetched = users_data_info["data"]["search"]['edges']
        # Check if data was fetched before accessing cursor
        if not users_data_fetched:
            logger.warning("No user data fetched in this iteration, stopping pagination.")
            break # Exit loop if no more data
        # update the cursor
        cursor = users_data_fetched[-1]["cursor"]
        number_of_users_fetched = len(users_data_fetched)
        all_number_of_users_fetched += number_of_users_fetched

        # the total count of github users
        users_total_count = users_data_info["data"]["search"]["userCount"]
        logger.info(f"Fetched {all_number_of_users_fetched}/{max_number_of_users} users | Total users: {users_total_count} ")
        # update update_at field with current datetime using the constant format
        updated_at = datetime.datetime.now().strftime(DATETIME_FORMAT)
        all_users_data['meta'].update({
            "updated_at": updated_at,
            "users_total_count": users_total_count,
            "top_users_count": all_number_of_users_fetched
        })
        # accumulate the users_data_fetched into the all_users_data

        # Update total counts including fetched counts

        users_data_fetched_adjusted_list = _process_user_data(users_data_fetched, updated_at)

        all_users_data["top_users"] += users_data_fetched_adjusted_list
        # save users_data_fetched_adjusted_list to sqlite specified db
        save_users(config.USERS_SQLITE_DB_PATH,
                   users_data_fetched_adjusted_list)

    # Update total counts including fetched counts after the loop finishes
    update_total_count(db_path=config.GITHUB_DB_INFO_PATH,
                       user_total_count=users_total_count, 
                       fetched_users_count=all_number_of_users_fetched,
                       repo_total_count=0,
                       fetched_repos_count=0)

    # save all_users_data to json file
    save_json(all_users_data,
              os.path.join(config.DATA_DIR, config.ORI_TOP_USERS_FILENAME))
    return all_users_data


def _process_user_data(users_data_fetched, updated_at):
    """Processes raw user data fetched from GraphQL API."""
    processed_users = []
    for user_data in users_data_fetched:
        node = user_data.get('node', {})
        if not node: # Skip if node is missing or empty
            logger.warning(f"Skipping user data due to missing 'node': {user_data}")
            continue

        followers_data = node.get('followers', {})
        top_repos_nodes = node.get('topRepositories', {}).get('nodes', [])

        processed_users.append({
            "databaseId": node.get('databaseId'),
            "id": node.get('id'),
            "login": node.get('login'),
            "name": node.get('name'),
            "avatarUrl": node.get('avatarUrl'),
            "url": node.get('url'),
            "followersCount": followers_data.get('totalCount'),
            "topRepositories_starsgazerCount": sum(
                repos.get("stargazerCount", 0) for repos in top_repos_nodes
            ),
            "updatedAt": updated_at
        })
    return processed_users


@retry_on_network_error(max_retries=3, delay=2)
def fetch_top_repos_by_graphql(number_of_repos: int = 10,
                               cursor: Optional[str] = None):
    url = f"{config.API_BASE_URL}/graphql"
    payload = {
        "query": GET_TOP_REPOS_QUERY,
        "operationName": "getToprepos",
        "variables": {
            "queryString": "stars:>0 sort:stars-desc",
            "number_of_repos": number_of_repos,
            "cursor": cursor
        }
    }
    time.sleep(config.WAIT_TIME_PER_REQUEST)
    response = requests.request("POST",
                                url,
                                json=payload,
                                headers=config.HEADERS)
    if response.status_code == 429:
        logger.warning("Too many requests, sleeping for 10 seconds")
        time.sleep(10)
        return fetch_top_repos_by_graphql(number_of_repos, cursor)
    elif response.status_code == 403:
        logger.exception(f"Error fetching top repos: [{response.status_code}]")
        logger.info(response.text) # Keep logging response text for context
        return None
    elif response.status_code != 200:
        # Use logger.error instead of logger.exception for non-200 status codes
        logger.error(f"Error fetching top repos: [{response.status_code}]")
        logger.info(response.text) # Keep logging response text for context
    response.raise_for_status()
    return response.json()


def fetch_all_repos_by_graphql(max_number_of_repos: int = 200,
                               number_of_repos_one_time: int = 100):
    # how to aggregate the data
    cursor = None  # initialize the cursor
    all_number_of_repos_fetched = 0
    repos_total_count = 0
    all_repos_data = {
        "meta": {
            "updated_at": "2016-01-01T00:00:00Z",
            "repos_total_count": 0,
            "top_repos_count": 0,
            "order_by": "stars",
            "order_direction": "desc"
        },
        "top_repos": []
    }
    if max_number_of_repos == -1:
        logger.info("No limit, fetching all repos from GitHub")
    while ((max_number_of_repos == -1) or (all_number_of_repos_fetched < max_number_of_repos)):
        repos_data_info = fetch_top_repos_by_graphql(number_of_repos_one_time,
                                                     cursor)
        if not repos_data_info:
            logger.warning("No repos data fetched in this iteration, stopping pagination.")
            break # Exit loop if no more data
        try:
            repos_data_fetched = repos_data_info["data"]["search"]['edges']
        except Exception as e:
            logger.exception(f"Error fetching top repos: [{e}]")
            logger.info(repos_data_info)
            raise e
        # Check if data was fetched before accessing cursor
        if not repos_data_fetched:
            logger.warning("No repo data fetched in this iteration, stopping pagination.")
            logger.info(f"cursors:{last_cursor} | current repos data info: {repos_data_info}")
            break # Exit loop if no more data
        # update the cursor
        cursor = repos_data_fetched[-1]["cursor"]
        ## debug
        last_cursor =cursor
        number_of_repos_fetched = len(repos_data_fetched)
        all_number_of_repos_fetched += number_of_repos_fetched
        # the total count of github users
        repos_total_count = repos_data_info["data"]["search"]["repositoryCount"]
        # update the total count of github repos
        if  max_number_of_repos == -1:
            max_number_of_repos = repos_total_count
         # update update_at field with current datetime using the constant format
        updated_at = datetime.datetime.now().strftime(DATETIME_FORMAT)
        all_repos_data['meta'].update({
            "updated_at": updated_at,
            "repos_total_count": repos_total_count,
            "top_repos_count": all_number_of_repos_fetched
        })
        # Process and accumulate the fetched repo data
        repos_data_fetched_adjusted_list = _process_repo_data(repos_data_fetched)
        all_repos_data["top_repos"] += repos_data_fetched_adjusted_list

        logger.info(
            f"Fetched {all_number_of_repos_fetched}/{max_number_of_repos} repos | Total repos: {repos_total_count} "
        )
        # save repos_data_fetched_adjusted_list to sqlite specified db
        save_repositories(config.REPOS_SQLITE_DB_PATH,
                          repos_data_fetched_adjusted_list)

    # Update total counts including fetched counts after the loop finishes
    update_total_count(db_path=config.GITHUB_DB_INFO_PATH,
                       repo_total_count=repos_total_count,
                       fetched_repos_count=all_number_of_repos_fetched)

    # save all_repos_data to json file
    save_json(all_repos_data,
              os.path.join(config.DATA_DIR, config.ORI_TOP_REPOS_FILENAME))
    
    logger.info(
        f"All repos data saved to {os.path.join(config.DATA_DIR, config.ORI_TOP_REPOS_FILENAME)}"
    )
    return all_repos_data

def _process_repo_data(repos_data_fetched: List[Dict]):
    """Processes raw repository data fetched from GraphQL API."""
    processed_repos = []
    for repo_data in repos_data_fetched:
        if not repo_data:
            logger.warning(f"Skipping repo data due to missing 'node': {repo_data}")
            continue
        node = repo_data.get('node', {})
        if not node: # Skip if node is missing or empty
            logger.warning(f"Skipping repo data due to missing 'node': {repo_data}")
            continue

        languages_nodes = node.get('languages', {}).get('nodes', [])

        processed_repos.append({
            "databaseId": node.get('databaseId'),
            "id": node.get('id'),
            "name": node.get('name'),
            "url": node.get('url'),
            "stargazerCount": node.get('stargazerCount'),
            "description": node.get('description'),
            "createdAt": node.get('createdAt'),
            "languages": [lang.get("name") for lang in languages_nodes if lang.get("name")]
        })
    return processed_repos


# --- Data Update Functions ---

def update_accumulatedStars_1d():
    """更新数据库中 accumulatedStars_1d 字段的值"""
    logger.info("Updating accumulatedStars_1d field...") # Changed print to logger.info
    repo_db_path = config.REPOS_SQLITE_DB_PATH
    # 1. 获取昨天的日期
    archived_top_repos = read_archived_top_repos_1d_before_today()
    if archived_top_repos is None:
        logger.warning("No archived top repos found.")
        return
    else:
        batch_update_accumulated_stars(repo_db_path, archived_top_repos,
                                       "accumulatedStars_1d")


def update_accumulatedStars_7d():
    """更新数据库中 accumulatedStars_7d 字段的值"""
    logger.info("Updating accumulatedStars_7d field...") # Changed print to logger.info
    repo_db_path = config.REPOS_SQLITE_DB_PATH
    archived_top_repos = read_archived_top_repos_7d_before_today()
    if archived_top_repos is None:
        logger.warning("No archived top repos found.")
        return
    else:
        batch_update_accumulated_stars(repo_db_path, archived_top_repos,
                                       "accumulatedStars_7d")


def update_accumulatedStars_30d():
    """更新数据库中 accumulatedStars_30d 字段的值"""
    logger.info("Updating accumulatedStars_30d field...") # Changed print to logger.info
    repo_db_path = config.REPOS_SQLITE_DB_PATH
    archived_top_repos = read_archived_top_repos_30d_before_today()

    if archived_top_repos is None:
        logger.warning("No archived top repos found.")
        return
    else:
        batch_update_accumulated_stars(repo_db_path, archived_top_repos,
                                       "accumulatedStars_30d")


# --- JSON Generation ---

def _generate_and_save_json(data_fetch_func, db_path, filename, data_key, count_key, order_by, order_direction, base_meta, **kwargs):
    """Helper function to fetch data, generate JSON structure, and save it."""
    logger.info(f"Generating {filename}...")
    items = data_fetch_func(db_path, **kwargs)
    data_structure = {
        "meta": {
            "updated_at": datetime.datetime.now().strftime(DATETIME_FORMAT), # Use constant format
            count_key: len(items),
            "order_by": order_by,
            "order_direction": order_direction,
        },
        data_key: items
    }
    data_structure['meta'].update(base_meta)
    save_json(data_structure, os.path.join(config.DATA_DIR, filename))
    logger.info(f"Generated {filename} with {len(items)} items.")

def generate_repo_json_files(base_meta):
    """Generate JSON files related to repositories."""
    logger.info("Generating repository JSON files...")
    repo_db_path = config.REPOS_SQLITE_DB_PATH
    repo_tasks = [
        {
            "func": get_repos_hot,
            "db": repo_db_path,
            "file": config.TOP_REPOS_FILENAME,
            "data_key": "top_repos",
            "count_key": "top_repos_count",
            "order": "stars",
            "dir": "desc",
            "kwargs": {'limit': config.TOP_REPOS_LIMIT}
        },
        {
            "func": get_repos_hot_order_by_range_day,
            "db": repo_db_path,
            "file": config.DAILY_TRENDING_FILENAME,
            "data_key": "top_repos",
            "count_key": "top_repos_count",
            "order": "stars_1d",
            "dir": "desc",
            "kwargs": {"range_day": 1, "limit": config.TRENDING_REPO_LIMIT}
        },
        {
            "func": get_repos_hot_order_by_range_day,
            "db": repo_db_path,
            "file": config.WEEKLY_TRENDING_FILENAME,
            "data_key": "top_repos",
            "count_key": "top_repos_count",
            "order": "stars_7d",
            "dir": "desc",
            "kwargs": {"range_day": 7}
        },
        {
            "func": get_repos_hot_order_by_range_day,
            "db": repo_db_path,
            "file": config.MONTHLY_TRENDING_FILENAME,
            "data_key": "top_repos",
            "count_key": "top_repos_count",
            "order": "stars_30d",
            "dir": "desc",
            "kwargs": {"range_day": 30}
        },
    ]
    for task in repo_tasks:
        try:
            _generate_and_save_json(
                data_fetch_func=task["func"],
                db_path=task["db"],
                filename=task["file"],
                data_key=task["data_key"],
                count_key=task["count_key"],
                order_by=task["order"],
                order_direction=task["dir"],
                base_meta=base_meta,
                **task["kwargs"]
            )
        except Exception as e:
            logger.error(f"Failed to generate {task['file']}: {e}", exc_info=True)
    logger.info("Finished generating repository JSON files.")

def generate_user_json_files(base_meta):
    """Generate JSON files related to users."""
    logger.info("Generating user JSON files...")
    user_db_path = config.USERS_SQLITE_DB_PATH
    user_tasks = [
        {
            "func": get_top_followergazer_count_users,
            "db": user_db_path,
            "file": config.TOP_USERS_FILENAME,
            "data_key": "top_users",
            "count_key": "top_users_count",
            "order": "followersCount",
            "dir": "desc",
            "kwargs": {'limit': config.TOP_USERS_LIMIT}
        },
    ]
    for task in user_tasks:
        try:
            _generate_and_save_json(
                data_fetch_func=task["func"],
                db_path=task["db"],
                filename=task["file"],
                data_key=task["data_key"],
                count_key=task["count_key"],
                order_by=task["order"],
                order_direction=task["dir"],
                base_meta=base_meta,
                **task["kwargs"]
            )
        except Exception as e:
            logger.error(f"Failed to generate {task['file']}: {e}", exc_info=True)
    logger.info("Finished generating user JSON files.")

def generate_trending_json_files():
    """从数据库查询数据并生成 JSON 文件 (Deprecated, use generate_repo_json_files and generate_user_json_files)"""
    logger.warning("generate_trending_json_files is deprecated. Use generate_repo_json_files and generate_user_json_files instead.")
    # Keep the old logic for compatibility or remove if sure it's not needed

    try:
        repos_total_count, user_total_count, _, _  = get_total_count_by_datetime(
            config.GITHUB_DB_INFO_PATH,
            datetime.datetime.now().strftime("%Y%m%d"))
    except Exception as e:
        logger.error(f"Failed to get total counts: {e}")
        repos_total_count, user_total_count, _, _ = 0, 0, 0, 0

    base_meta = {
        "repos_total_count": repos_total_count,
        "user_total_count": user_total_count,
    }
    generate_repo_json_files(base_meta)
    generate_user_json_files(base_meta)


def check_db_size():
    for db_path in config.SQLITE_DB_PATHS:
        logger.info(f"Checking database size for {db_path}...")
        try:
            db_size = os.path.getsize(db_path) / (1024 * 1024)  # Size in MB
            logger.info(f"Database size: {db_size:.2f} MB") # Changed print to logger.info
            if db_size > 100:
                logger.warning("Warning: Database size exceeds 100MB limit!")
                # Consider exiting with non-zero code for CI/CD pipelines
                # exit(1)
            else:
                logger.info("Database size within limits.")
        except FileNotFoundError:
            logger.exception(
                f"Warning: Database file not found at {db_path} for size check."
            )
        except Exception as e:
            logger.exception(f"Error checking database size: {e}")


# --- Main Execution ---


def initialize_database():
    """初始化数据库目录"""
    logger.info("Initializing Database")
    os.makedirs(config.DATA_DIR, exist_ok=True)


def fetch_data():
    """获取GitHub用户和仓库数据"""
    logger.info("Starting Data Fetching")
    try:
        fetch_all_repos_by_graphql(max_number_of_repos=config.MAX_REPOS, number_of_repos_one_time=config.REPOS_ONE_TIME)
        fetch_all_users_by_graphql(max_number_of_users=config.MAX_USERS, number_of_users_one_time=config.USERS_ONE_TIME, usertopRepositories_count=config.USER_TOP_REPOSITORIES_COUNT)
        logger.info("Finished Data Fetching")
    except Exception as e:
        logger.exception(f"Data fetching failed: {e}:")
        raise


def update_stars_data():
    """更新星标统计数据"""
    logger.info("Updating Stars Data")
    try:
        update_accumulatedStars_1d()
        update_accumulatedStars_7d()
        update_accumulatedStars_30d()
    except Exception as e:
        logger.error(f"Failed to update stars data: {e}")
        raise


def generate_json_files():
    """生成JSON文件"""
    logger.info("Starting JSON Generation")
    try:
        generate_trending_json_files()
        logger.info("Finished JSON Generation")
    except Exception as e:
        logger.error(f"JSON generation failed: {e}")
        raise


def archive_and_save():
    """归档数据并保存更新时间"""
    logger.info("Starting Archiving")
    try:
        archive_data()
        save_update_time()
        logger.info("Finished Archiving")
    except Exception as e:
        logger.error(f"Archiving failed: {e}")
        raise


def run_pipeline():
    """Runs the full data fetching and processing pipeline."""
    steps = [
        ("Initializing Database", initialize_database),
        ("Fetching Data", fetch_data),
        ("Updating Stars Data", update_stars_data),
        ("Generating JSON Files", generate_json_files),
        ("Archiving Data", archive_and_save),
        ("Checking DB Size", check_db_size),
    ]

    for name, step_func in steps:
        logger.info(f"--- Starting Step: {name} ---")
        try:
            step_func()
            logger.info(f"--- Finished Step: {name} ---")
        except Exception as e:
            logger.error(f"--- Step Failed: {name} - {e} ---")
            # Optionally re-raise the exception if one step failure should stop the whole pipeline
            # raise
            return False # Indicate failure
    return True # Indicate success

def main():
    if run_pipeline():
        logger.info("Script finished successfully")
        return 0
    else:
        logger.error("Script finished with errors")
        return 1


if __name__ == "__main__":
    exit(main())
