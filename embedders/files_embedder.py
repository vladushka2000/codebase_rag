import cocoindex

from config import ai_config, pg_config
from embedders import utils

ai_config_ = ai_config.AIConfig()
pg_config_ = pg_config.PostgresConfig()


@cocoindex.flow_def(name="FilesEmbedding")
def files_embedding_flow(flow_builder: cocoindex.FlowBuilder, data_scope: cocoindex.DataScope) -> None:
    """
    Cocoindex files embedding flow
    :param flow_builder: flow builder
    :param data_scope: data scope
    """

    data_scope["files"] = flow_builder.add_source(
        cocoindex.sources.Postgres(
            table_name="files",
            included_columns=[
                "path",
                "content",
            ]
        )
    )
    files_embeddings = data_scope.add_collector()

    with data_scope["files"].row() as file:
        file["extension"] = flow_builder.transform(
            utils.extract_extension_from_path,
            file["path"],
        )
        file["lang"] = flow_builder.transform(
            utils.get_language,
            file["extension"],
        )
        file["chunks"] = file["content"].transform(
            cocoindex.functions.SplitRecursively(),
            language=file["extension"],
            chunk_size=ai_config_.embedder_chunk_size,
            chunk_overlap=ai_config_.embedder_chunk_overlap,
        )

        with file["chunks"].row() as chunk:
            chunk["embedding"] = utils.code_to_embedding(chunk["text"])
            files_embeddings.collect(
                path=file["path"],
                location=chunk["location"],
                content=chunk["text"],
                embedding=chunk["embedding"],
            )

    files_embeddings.export(
        "file_chunks",
        cocoindex.storages.Postgres(
            table_name="file_chunks",
        ),
        primary_key_fields=["id",],
        vector_indexes=[
            cocoindex.VectorIndexDef(
                field_name="embedding",
                metric=cocoindex.VectorSimilarityMetric.COSINE_SIMILARITY,
            )
        ],
    )
