import datetime

from config import logger
from typing import Tuple, Optional, Type
from contextlib import contextmanager

from .database_adapter import SQLiteAdapter
from .models import GithubInfo, Repository, User


from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

def get_engine_and_session(db_path: str) -> Tuple[Engine, Type[Session]]:
    """获取数据库引擎和会话类。

    Args:
        db_path (str): 数据库文件的路径。

    Returns:
        Tuple[Engine, Type[Session]]: 数据库引擎和 SQLAlchemy 会话类。
    """
    adapter = SQLiteAdapter()
    return adapter.get_engine_and_session(db_path)


from collections.abc import Generator

@contextmanager
def session_scope(db_path: str) -> Generator[Session, None, None]:
    """提供一个围绕一系列操作的事务作用域。

    确保会话被正确提交或回滚，并在最后关闭。

    Args:
        db_path (str): 数据库文件的路径。

    Yields:
        Session: SQLAlchemy 会话实例。
    """
    _, Session = get_engine_and_session(db_path)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception("Session rollback due to exception:")
        raise e
    finally:
        session.close()


from typing import List, Dict, Tuple, Optional, Type

def init_db(db_path: str):
    """初始化数据库，如果不存在则创建表结构。

    Args:
        db_path (str): 数据库文件的路径。
    """
    adapter = SQLiteAdapter()
    adapter.init_db(db_path)


def save_users(db_path: str, users: List[Dict]):
    """将用户数据批量保存或更新到数据库（ORM方式）。

    Args:
        db_path (str): 数据库文件的路径。
        users (List[Dict]): 包含用户数据的字典列表。
    """
    with session_scope(db_path) as session:
        for item in users:
            user = session.query(User).filter_by(
                databaseId=item.get('databaseId')).first()
            if not user:
                user = User(databaseId=item.get('databaseId'))
            # Update user attributes safely using .get with defaults
            user.login = item.get('login')
            user.name = item.get('name')
            user.id = item.get('id')
            user.avatarUrl = item.get('avatarUrl')
            user.url = item.get('url')
            user.followersCount = item.get('followersCount')
            user.topRepositories_starsgazerCount = item.get(
                'topRepositories_starsgazerCount')
            user.updatedAt = datetime.datetime.now()
            session.merge(user)
    logger.info(f"{len(users)} Users saved to {db_path}")


def save_repositories(db_path: str, repos: List[Dict]):
    """将仓库数据批量保存或更新到数据库（ORM方式）。

    Args:
        db_path (str): 数据库文件的路径。
        repos (List[Dict]): 包含仓库数据的字典列表。
    """
    with session_scope(db_path) as session:
        for item in repos:
            repo = session.query(Repository).filter_by(
                databaseId=item.get('databaseId')).first()
            if not repo:
                repo = Repository(databaseId=item.get('databaseId'))

            # Update repo attributes safely
            repo.id = item.get('id')
            repo.name = item.get('name')
            repo.url = item.get('url')
            languages = item.get('languages', [])
            repo.language = ' | '.join(languages) if languages else None
            repo.description = item.get('description')
            repo.accumulatedStars = item.get('stargazerCount')
            # These fields might not be present in the initial fetch, handle None
            repo.accumulatedStars_1d = item.get('accumulatedStars_1d')
            repo.accumulatedStars_7d = item.get('accumulatedStars_7d')
            repo.accumulatedStars_30d = item.get('accumulatedStars_30d')
            created_at_str = item.get('createdAt')
            if created_at_str:
                try:
                    repo.createdAt = datetime.datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                     logger.warning(f"Invalid createdAt format for repo {repo.databaseId}: {created_at_str}")
                     repo.createdAt = None # Or set a default
            else:
                repo.createdAt = None

            repo.updatedAt = datetime.datetime.now()
            session.merge(repo)
    logger.info(f"{len(repos)} repos saved to {db_path}")


# get repo data from database by databaseId
def get_repo(db_path: str, databaseId: int) -> Optional[Repository]:
    """通过 databaseId 查询单个仓库。

    Args:
        db_path (str): 数据库文件的路径。
        databaseId (int): GitHub 仓库的 databaseId。

    Returns:
        Optional[Repository]: 找到的仓库对象，如果未找到则返回 None。
    """
    with session_scope(db_path) as session:
        return session.query(Repository).filter_by(
            databaseId=databaseId).first()


# update repo data by databaseId
def update_repo(db_path: str, databaseId: int, data: Dict):
    """通过 databaseId 更新单个仓库的数据。

    Args:
        db_path (str): 数据库文件的路径。
        databaseId (int): GitHub 仓库的 databaseId。
        data (Dict): 要更新的字段和值的字典。
    """
    with session_scope(db_path) as session:
        repo = session.query(Repository).filter_by(
            databaseId=databaseId).first()
        if repo:
            for key, value in data.items():
                # Basic validation to prevent setting non-existent attributes
                if hasattr(repo, key):
                    setattr(repo, key, value)
                else:
                    logger.warning(f"Attempted to set non-existent attribute '{key}' on Repository {databaseId}")
            # Ensure updatedAt is always updated
            repo.updatedAt = datetime.datetime.now()
            # The commit is handled by session_scope


# get repos data from database order by accumulatedStars desc
def get_repos_hot(db_path: str, limit: int = 100) -> List[Dict]:
    """查询热门仓库 (按总 star 数降序排序)。

    Args:
        db_path (str): 数据库文件的路径。
        limit (int): 返回的仓库数量上限。 -1 表示返回所有数据。

    Returns:
        List[Dict]: 仓库数据字典的列表。
    """

    with session_scope(db_path) as session:
        if limit == -1:
            repos_list = session.query(Repository).all()
        else:
            repos_list = session.query(Repository).order_by(
            Repository.accumulatedStars.desc()).limit(limit).all()
        
        return [repo.as_dict() for repo in repos_list]


def update_accumulated_stars_by_db_id(db_path: str, databaseId: int,
                                      accumulated_stars_key: str,
                                      accumulated_stars_value: int):
    """通过 databaseId 更新仓库指定的 star 统计字段。

    Args:
        db_path (str): 数据库文件的路径。
        databaseId (int): GitHub 仓库的 databaseId。
        accumulated_stars_key (str): 要更新的 star 统计字段名 (如 'accumulatedStars_1d')。
        accumulated_stars_value (int): 新的 star 统计值。

    Raises:
        ValueError: 如果 accumulated_stars_key 无效。
    """
    valid_keys = ['accumulatedStars', 'accumulatedStars_1d', 'accumulatedStars_7d', 'accumulatedStars_30d']
    if accumulated_stars_key not in valid_keys:
        raise ValueError(f'accumulated_stars_key must be one of {valid_keys}')

    with session_scope(db_path) as session:
        repo = session.query(Repository).filter_by(databaseId=databaseId).first()
        if repo:
            setattr(repo, accumulated_stars_key, accumulated_stars_value)
            repo.updatedAt = datetime.datetime.now()
            # Commit handled by session_scope
        else:
            logger.warning(f"Repo with databaseId {databaseId} not found for update")


# get repos data from database order by accumulatedStars_1d desc
def get_repos_hot_order_by_range_day(db_path: str, range_day: int, limit: int = 100) -> List[Dict]:
    """查询指定时间范围内的热门仓库 (按对应时间范围的 star 增长数降序排序)。

    Args:
        db_path (str): 数据库文件的路径。
        range_day (int): 时间范围 (1, 7, 或 30)。
        limit (int): 返回的仓库数量上限。

    Returns:
        List[Dict]: 仓库数据字典的列表。

    Raises:
        ValueError: 如果 range_day 无效。
    """
    valid_range_days = {1, 7, 30}
    if range_day not in valid_range_days:
        raise ValueError(f'range_day must be one of {valid_range_days}')

    order_by_column = {
        1: Repository.accumulatedStars_1d,
        7: Repository.accumulatedStars_7d,
        30: Repository.accumulatedStars_30d
    }.get(range_day)

    with session_scope(db_path) as session:
        repos_list = session.query(Repository).order_by(
            order_by_column.desc()).limit(limit).all()
        return [repo.as_dict() for repo in repos_list]


from sqlalchemy import Column

# get top users based on a specific metric
def _get_top_users_by_metric(db_path: str, metric_column: Column, limit: int = 100) -> List[Dict]:
    """辅助函数：按指定指标列查询 Top 用户。

    Args:
        db_path (str): 数据库文件的路径。
        metric_column (Column): 用于排序的 SQLAlchemy 列对象。
        limit (int): 返回的用户数量上限。

    Returns:
        List[Dict]: 用户数据字典的列表。
    """
    with session_scope(db_path) as session:
        users_list = session.query(User).order_by(
            metric_column.desc()).limit(limit).all()
        return [user.as_dict() for user in users_list]

# get top starsgazer users
def get_top_starsgazer_count_users(db_path: str, limit: int = 100) -> List[Dict]:
    """查询 Top 仓库总 star 数最多的用户。

    Args:
        db_path (str): 数据库文件的路径。
        limit (int): 返回的用户数量上限。

    Returns:
        List[Dict]: 用户数据字典的列表。
    """
    return _get_top_users_by_metric(db_path, User.topRepositories_starsgazerCount, limit)


# get top follower users
def get_top_followergazer_count_users(db_path: str, limit: int = 100) -> List[Dict]:
    """查询粉丝数最多的用户。

    Args:
        db_path (str): 数据库文件的路径。
        limit (int): 返回的用户数量上限。

    Returns:
        List[Dict]: 用户数据字典的列表。
    """
    return _get_top_users_by_metric(db_path, User.followersCount, limit)


def batch_update_accumulated_stars(db_path: str, top_repos_data: Dict,
                                   accumulated_stars_key: str):
    """根据前一天的 star 数，批量计算并更新仓库在指定时间范围内的 star 增长数。

    Args:
        db_path (str): 当前数据库文件的路径。
        top_repos_data (Dict): 从归档数据中读取的仓库数据字典，
                               格式如 {'top_repos': [{'databaseId': 123, 'accumulatedStars': 100}, ...]}。
        accumulated_stars_key (str): 要更新的 star 增长数字段名
                                     ('accumulatedStars_1d', 'accumulatedStars_7d', 'accumulatedStars_30d')。
    """
    valid_keys = ['accumulatedStars_1d', 'accumulatedStars_7d', 'accumulatedStars_30d']
    if accumulated_stars_key not in valid_keys:
        logger.error(f"Invalid accumulated_stars_key: {accumulated_stars_key}")
        return

    if not top_repos_data or 'top_repos' not in top_repos_data:
        logger.warning("No top_repos data provided for batch update.")
        return

    updates_count = 0
    with session_scope(db_path) as session:
        # Fetch all relevant repos in one go for potential optimization
        # repo_ids = [item['databaseId'] for item in top_repos_data['top_repos']]
        # existing_repos = {repo.databaseId: repo for repo in session.query(Repository).filter(Repository.databaseId.in_(repo_ids)).all()}

        for repo_item in top_repos_data['top_repos']:
            repo_db_id = repo_item.get('databaseId')
            archived_stargazer_count = repo_item.get('accumulatedStars')

            if repo_db_id is None or archived_stargazer_count is None:
                logger.warning(f"Skipping item due to missing data: {repo_item}")
                continue

            # repo = existing_repos.get(repo_db_id) # Use pre-fetched repo if optimization is applied
            repo = session.query(Repository).filter_by(databaseId=repo_db_id).first()

            if repo:
                if repo.accumulatedStars is not None:
                    star_diff = repo.accumulatedStars - archived_stargazer_count
                    setattr(repo, accumulated_stars_key, star_diff)
                    repo.updatedAt = datetime.datetime.now()
                    updates_count += 1
                    # Commit is handled by session_scope
                else:
                    logger.warning(f"Repo {repo_db_id} has None for accumulatedStars, cannot calculate diff.")
            else:
                logger.warning(f"Repo {repo_db_id} not found in database during batch update")
    logger.info(f"Batch updated {updates_count} repos for key '{accumulated_stars_key}' in {db_path}")


def update_total_count(db_path: str, 
                       repo_total_count: Optional[int] = None, 
                       user_total_count: Optional[int] = None,
                       fetched_repos_count: Optional[int] = None,
                       fetched_users_count: Optional[int] = None):
    """更新或创建当天的仓库和用户总数以及实际抓取数量记录。

    Args:
        db_path (str): GithubInfo 数据库文件的路径。
        repo_total_count (Optional[int]): 最新的仓库总数，如果为 None 则不更新。
        user_total_count (Optional[int]): 最新的用户总数，如果为 None 则不更新。
        fetched_repos_count (Optional[int]): 当天实际抓取的仓库数，如果为 None 则不更新。
        fetched_users_count (Optional[int]): 当天实际抓取的用户数，如果为 None 则不更新。
    """
    with session_scope(db_path) as session:
        dt = datetime.datetime.now().strftime("%Y%m%d")
        github_info = session.query(GithubInfo).filter_by(dt=dt).first()

        if not github_info:
            logger.info(f"Creating new GithubInfo record for date {dt} in {db_path}")
            github_info = GithubInfo(dt=dt)
            session.add(github_info) # Add the new instance to the session

        updated = False
        if user_total_count is not None and github_info.usersCount != user_total_count:
            github_info.usersCount = user_total_count
            updated = True
        if repo_total_count is not None and github_info.reposCount != repo_total_count:
            github_info.reposCount = repo_total_count
            updated = True
        if fetched_repos_count is not None and github_info.fetchedReposCount != fetched_repos_count:
            github_info.fetchedReposCount = fetched_repos_count
            updated = True
        if fetched_users_count is not None and github_info.fetchedUsersCount != fetched_users_count:
            github_info.fetchedUsersCount = fetched_users_count
            updated = True

        if updated:
             # Commit is handled by session_scope
            logger.info(
                f"Updated counts for {dt}: TotalRepos={github_info.reposCount}, TotalUsers={github_info.usersCount}, "
                f"FetchedRepos={github_info.fetchedReposCount}, FetchedUsers={github_info.fetchedUsersCount} in {db_path}"
            )
        else:
            logger.info(f"Counts for {dt} remain unchanged in {db_path}")


# get the total count of repos by dt
def get_total_count_by_datetime(db_path: str, date_str: str) -> Tuple[int, int]:
    """获取指定日期 (YYYYMMDD) 的仓库和用户总数。

    Args:
        db_path (str): GithubInfo 数据库文件的路径。
        date_str (str): 日期字符串，格式为 'YYYYMMDD'。

    Returns:
        Tuple[int, int]: 一个包含仓库总数和用户总数的元组 (repos_count, users_count)。
                         如果找不到对应日期的记录，则返回 (0, 0)。
    """
    with session_scope(db_path) as session:
        github_info = session.query(GithubInfo).filter_by(dt=date_str).first()
        if github_info:
            return github_info.reposCount or 0, github_info.usersCount or 0
        else:
            logger.warning(f"No GithubInfo found for date {date_str} in {db_path}")
            return 0, 0
