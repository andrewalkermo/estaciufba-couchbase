import threading
import time

import couchbase
from couchbase.options import ReplaceOptions
from couchbase.exceptions import CASMismatchException, DocumentExistsException
from couchbase.management.logic.users_logic import Role, User
from couchbase.management.logic.view_index_logic import DesignDocument, DesignDocumentNamespace, View
from couchbase.management.options import CreatePrimaryQueryIndexOptions
from couchbase.management.queries import CollectionQueryIndexManager
from couchbase.management.views import ViewIndexManager

from db import  Database

db = Database()

def inserir_dados():
    db.scope.collection("estacionamentos").upsert("estacionamento::1", {
        "nome": "Estação 7 UFBA Portaria 1",
        "campus": "Ondina",
        "localizacao": {
            "x": -13.002689819109012,
            "y": -38.507009500556485
        }
    })
    db.scope.collection("vagas").upsert("vaga::1", {
        "estacionamento_id": "estacionamento::1",
        "disponivel": True,
        "status": "livre"
    })

    db.scope.collection("vagas").upsert("vaga::2", {
        "estacionamento_id": "estacionamento::1",
        "disponivel": True,
        "status": "livre"
    })

    db.scope.collection("vagas_acessos").upsert("vaga_acesso::1", {
        "vaga_id": "vaga::1",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::2", {
        "vaga_id": "vaga::1",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::3", {
        "vaga_id": "vaga::1",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::4", {
        "vaga_id": "vaga::1",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::5", {
        "vaga_id": "vaga::1",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::6", {
        "vaga_id": "vaga::2",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::7", {
        "vaga_id": "vaga::2",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::8", {
        "vaga_id": "vaga::2",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })


def criar_indice():
    CollectionQueryIndexManager(
        connection=db.cluster.connection,
        bucket_name="estaciufba",
        scope_name="develop",
        collection_name="estacionamentos"
    ).create_primary_index(CreatePrimaryQueryIndexOptions(ignore_if_exists=True))

    CollectionQueryIndexManager(
        connection=db.cluster.connection,
        bucket_name="estaciufba",
        scope_name="develop",
        collection_name="vagas"
    ).create_primary_index(CreatePrimaryQueryIndexOptions(ignore_if_exists=True))

    CollectionQueryIndexManager(
        connection=db.cluster.connection,
        bucket_name="estaciufba",
        scope_name="develop",
        collection_name="vagas_acessos"
    ).create_primary_index(CreatePrimaryQueryIndexOptions(ignore_if_exists=True))

    db.scope.collection("estacionamentos").query_indexes().create_index(
        index_name="idx_nome",
        fields=["nome"],
        ignore_if_exists=True
    )

    db.scope.collection("vagas").query_indexes().create_index(
        index_name="idx_estacionamento_id",
        fields=["estacionamento_id", "disponivel"],
        ignore_if_exists=True
    )

    db.scope.collection("vagas_acessos").query_indexes().create_index(
        index_name="idx_vaga_id",
        fields=["vaga_id", "entrada"],
        ignore_if_exists=True
    )

def criar_views():
    ViewIndexManager(
        connection=db.cluster.connection,
        bucket_name="estaciufba",
    ).upsert_design_document(
        DesignDocument(
            'vagas_livres',
            {
                'vagas_livres': View (
                    """
                    function (doc, meta) {
                        if (doc.disponivel) {
                            emit(meta.id, doc);
                        }
                    }
                    """
                )
            },
            DesignDocumentNamespace.DEVELOPMENT
        ),
        DesignDocumentNamespace.DEVELOPMENT
    )

def criar_stored_procedures():
    query = """
            CREATE OR REPLACE FUNCTION qtd_vagas_no_estacionamento(estacionamentoId) { (
                SELECT COUNT(*)
                FROM vagas v
                WHERE v.estacionamento_id = 'estacionamento::1' AND v.disponivel = true 
            )}
            """
    db.scope.query(query)

def reservar_vaga(vaga_id):
    # get one where disponivel = true
    res = db.scope.collection("vagas").get(vaga_id)

    vaga_disponivel = res.content_as[dict]

    # update disponivel = false
    vaga_disponivel["disponivel"] = False

    try:
        print(f"Tentando reservar vaga {vaga_id}")

        db.scope.collection("vagas").replace(vaga_id, vaga_disponivel, ReplaceOptions(cas=res.cas))
    except (CASMismatchException, DocumentExistsException):
        raise Exception("Erro ao reservar vaga")

    print(f"Vaga reservada {vaga_id}")


def tentar_reservar_uma_vaga(estacionamento_id, tentativa=0):
    try:
        vaga = db.obter_vaga_livre(estacionamento_id)
        if not vaga or not vaga['disponivel']:
            raise Exception("Erro ao reservar vaga")

        reservar_vaga(vaga['id'])
    except Exception as e:
        if tentativa < 3:
            time.sleep(1)
            tentar_reservar_uma_vaga(estacionamento_id, tentativa+1)
        else:
            raise Exception("Erro ao reservar vaga")

def criar_usuario_ocupar_vagas():
    db.cluster.users().upsert_user(
        User(
            username="ocupar_vagas",
            password="ocupar_vagas",
            roles={
                Role( name="query_select", bucket="estaciufba", scope="develop", collection="estacionamentos"),
                Role( name="query_select", bucket="estaciufba", scope="develop", collection="vagas"),
                Role( name="query_select", bucket="estaciufba", scope="develop", collection="vagas_acessos"),
                Role( name="query_insert", bucket="estaciufba", scope="develop", collection="vagas_acessos"),
                Role( name="query_update", bucket="estaciufba", scope="develop", collection="vagas"),
            }
        )
    )

if __name__ == "__main__":
    inserir_dados()
    criar_indice()
    criar_views()
    criar_stored_procedures()
    criar_usuario_ocupar_vagas()

    # run reservar_vaga in two threads
    thread1 = threading.Thread(target=tentar_reservar_uma_vaga, args=("estacionamento::1",))
    thread2 = threading.Thread(target=tentar_reservar_uma_vaga, args=("estacionamento::1",))

    thread1.start()
    thread2.start()

