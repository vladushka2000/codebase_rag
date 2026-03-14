from typing import Dict, Any


class ToEmbedDTO:
    """
    Embed DTO mixin
    """

    def to_embedding_document(
        self,
        chunk_index: int,
        total_chunks: int,
        chunk_content: str,
    ) -> Dict[str, Any]:
        """
        Transform to embedding document
        """

        raise NotImplementedError
