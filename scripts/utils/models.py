from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

__all__ = ['User', 'Repository', 'GithubInfo', 'Base']

Base = declarative_base()


from typing import Dict, Any

class User(Base):
    """Represents a GitHub user in the database."""
    __tablename__ = 'users'
    id = Column(String, comment='GitHub Node ID')
    login = Column(String, comment='Username')
    name = Column(String, comment='Display name')
    databaseId = Column(Integer, primary_key=True, comment='GitHub Database ID')
    avatarUrl = Column(String, comment='Avatar URL')
    url = Column(String, comment='GitHub profile URL')
    followersCount = Column(Integer, comment='Number of followers')
    topRepositories_starsgazerCount = Column(Integer, comment='Total stars of top repositories')
    updatedAt = Column(DateTime, comment='Last update timestamp')

    def as_dict(self) -> Dict[str, Any]:
        """Converts the User model instance to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the user.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle JSON fields
            if isinstance(column.type, JSON):
                result[column.name] = value if value else []
            else:
                result[column.name] = value
        return result


class Repository(Base):
    """Represents a GitHub repository in the database."""
    __tablename__ = 'repositories'
    databaseId = Column(Integer, primary_key=True, comment='GitHub Database ID')
    id = Column(String, comment='GitHub Node ID')
    name = Column(String, comment='Repository name')
    url = Column(String, comment='Repository URL')
    language = Column(String, comment='Primary programming languages (pipe-separated)')
    description = Column(String, comment='Repository description')
    accumulatedStars = Column(Integer, comment='Total accumulated stars')
    # Star difference calculation fields
    accumulatedStars_1d = Column(Integer, comment='Star difference in the last 1 day', default=0)
    accumulatedStars_7d = Column(Integer, comment='Star difference in the last 7 days', default=0)
    accumulatedStars_30d = Column(Integer, comment='Star difference in the last 30 days', default=0)
    createdAt = Column(String, comment='Creation timestamp (ISO 8601 string)') # Kept as string based on db_utils usage
    updatedAt = Column(DateTime, comment='Last update timestamp')

    def as_dict(self) -> Dict[str, Any]:
        """Converts the Repository model instance to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the repository.
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle JSON fields
            if column.name == 'language':
                result[column.name] = value.split('|') if value else []
            else:
                result[column.name] = value
        return result


class GithubInfo(Base):
    """Stores daily counts of repositories and users from GitHub."""
    __tablename__ = 'githubinfo'
    dt = Column(String, comment='Date string (YYYYMMDD)', unique=True, primary_key=True)
    reposCount = Column(Integer, comment='Total repository count for the day', default=0)
    usersCount = Column(Integer, comment='Total user count for the day', default=0)
    fetchedReposCount = Column(Integer, comment='Actual fetched repository count for the day', default=0)
    fetchedUsersCount = Column(Integer, comment='Actual fetched user count for the day', default=0)
