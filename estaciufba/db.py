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
        self.cluster.wait_until_ready(timedelta(seconds=30))
        self.cb = self.cluster.bucket(bucket_name)
        self.scope = self.cb.scope("develop")

    def vagas_livres_do_estacionamento(self, estacionamento_id: str):
        query = """
            SELECT vagas.*
            FROM vagas
            WHERE estacionamento_id = $1 AND disponivel = true
            """
        return self.scope.query(query, QueryOptions(positional_parameters=[estacionamento_id]))

    def obter_vaga_livre(self, estacionamento_id: str):
        query = """
                SELECT META().id, vagas.*
                FROM vagas
                WHERE estacionamento_id = 'estacionamento::1' AND disponivel = true
                LIMIT 1
                """
        res = self.scope.query(query, QueryOptions(positional_parameters=[estacionamento_id])).execute()
        vaga = res[0] if res else None
        return vaga

    def ocupar_vaga_do_estacionamento(self, estacionamento_id: str, vaga_id: str):
        query = """
            UPDATE vagas
            SET disponivel = false
            WHERE estacionamento_id = $1 AND meta().id = $2
            RETURNING *
            """
        return self.scope.query(query, QueryOptions(positional_parameters=[estacionamento_id, vaga_id]))

    def registrar_acesso_vaga(self, vaga_id: str):
        query = """
            INSERT INTO vagas_acessos (KEY, VALUE)
            VALUES (CONCAT("vaga_acesso::", UUID()), {
                "vaga_id": $1,
                "entrada": NOW_MS(),
                "saida": null
            })
            """

    def ocupar_vaga(self, vaga_id: str):
        query = """
            BEGIN WORK;
            
            UPDATE vagas
            SET disponivel = false
            WHERE meta().id = $1;
            
            INSERT INTO vagas_acessos (KEY, VALUE)
            VALUES (CONCAT("vaga_acesso::", UUID()), {
                "vaga_id": $1,
                "entrada": NOW_MS(),
                "saida": null
            });
            
            COMMIT WORK;
            """
        return self.scope.query(query, QueryOptions(positional_parameters=[vaga_id]))

