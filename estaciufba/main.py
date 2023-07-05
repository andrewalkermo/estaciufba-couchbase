import couchbase
from couchbase.management.logic.view_index_logic import DesignDocument, DesignDocumentNamespace, View
from couchbase.management.options import CreatePrimaryQueryIndexOptions
from couchbase.management.queries import CollectionQueryIndexManager
from couchbase.management.views import ViewIndexManager

from db import  Database

db = Database()

def inserir_dados():
    resultado = db.scope.collection("estacionamentos").upsert("estacionamento::1", {
        "nome": "Estação 7 UFBA Portaria 1",
        "campus": "Ondina",
        "localizacao": {
            "x": -13.002689819109012,
            "y": -38.507009500556485
        }
    })
    resultado = db.scope.collection("vagas").upsert("vaga::1", {
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
        "vaga_id": "vaga::2",
        "entrada": "2023-01-01 00:00:00",
        "saida": "2023-01-01 00:00:00"
    })
    db.scope.collection("vagas_acessos").upsert("vaga_acesso::3", {
        "vaga_id": "vaga::1",
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


if __name__ == "__main__":
    inserir_dados()
    criar_indice()
    criar_views()
