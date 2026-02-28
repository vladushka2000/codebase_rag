from pydantic import Field
from pydantic_settings import BaseSettings

from utils import const


class AppConfig(BaseSettings):
    """
    App settings
    """

    language: const.Language = Field(
        default=const.Language.RU,
        description="App language",
    )
