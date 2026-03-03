import cocoindex

from config import pg_config
from embedders import files_embedder  # noqa

pg_config_ = pg_config.PostgresConfig()

cocoindex.init(
    settings=cocoindex.Settings(
        database=cocoindex.setting.DatabaseConnectionSpec(
            url=str(pg_config_.postgres_dsn),
            user=pg_config_.user,
            password=pg_config_.password,
        ),
    )
)
