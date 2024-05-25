from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from cognee.infrastructure.databases.relational import DuckDBAdapter


class RelationalConfig(BaseSettings):
    db_path: str =  "databases"
    db_name: str =  "cognee.db"
    db_host: str =  "localhost"
    db_port: str =  "5432"
    db_user: str = "cognee"
    db_password: str =  "cognee"
    db_engine: object = DuckDBAdapter(
        db_name=db_name,
        db_path=db_path
    )

    model_config = SettingsConfigDict(env_file = ".env", extra = "allow")

    def to_dict(self) -> dict:
        return {
            "db_path": self.db_path,
            "db_name": self.db_name,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_user": self.db_user,
            "db_password": self.db_password,
            "db_engine": self.db_engine
        }

@lru_cache
def get_relationaldb_config():
    return RelationalConfig()