import os
from datetime import timedelta
# needed for any cluster connection
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
# needed for options -- cluster, timeout, SQL++ (N1QL) query, etc.
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions,
                               QueryOptions)

class Database:
    def __init__(self):
        username = os.getenv("DB_PRINCIPAL_USERNAME")
        password = os.getenv("DB_PRINCIPAL_PASSWORD")
        bucket_name = "estaciufba"
        auth = PasswordAuthenticator(
            username,
            password,
        )
        self.cluster = Cluster('couchbase://db_principal', ClusterOptions(auth))
        self.cluster.wait_until_ready(timedelta(seconds=5))
        self.cb = self.cluster.bucket(bucket_name)
        self.scope = self.cb.scope("develop")

    def vagas_livres_do_estacionamento(self, estacionamento_id: str):
        query = """
            SELECT vagas.*
            FROM vagas
            WHERE estacionamento_id = $1 AND disponivel = true
        """
        return self.scope.query(query, QueryOptions(positional_parameters=[estacionamento_id]))