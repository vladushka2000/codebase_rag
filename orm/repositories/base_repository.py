from db_clients import alchemy_pg_client


class BaseAlchemyRepository:
    """
    Base repository for SQLAlchemy
    """

    def __init__(self, pg_client: alchemy_pg_client.AlchemyPGClient) -> None:
        """
        Init variables
        :param pg_client: Postgres alchemy client
        """

        self.pg_client = pg_client
