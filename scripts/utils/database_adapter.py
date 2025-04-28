import os
from abc import ABC, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    @abstractmethod
    def get_engine_and_session(self, connection_string):
        """获取数据库引擎和会话"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite数据库适配器"""

    def get_engine_and_session(self, db_path):
        data_dir = os.path.dirname(db_path)
        os.makedirs(data_dir, exist_ok=True)
        connection_string = f"sqlite:///{db_path}"
        engine = create_engine(connection_string)
        Base.metadata.create_all(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        return engine, Session
