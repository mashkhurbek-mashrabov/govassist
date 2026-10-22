from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from pgvector.django import HnswIndex, VectorField

from apps.common.models import BaseModel
from apps.corpus.constants import HNSW_EF_CONSTRUCTION, HNSW_M, SEARCH_CONFIG
from apps.corpus.models.document import Document


class Chunk(BaseModel):
    """A retrievable slice of a document with its embedding and FTS vector."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    order = models.PositiveIntegerField()
    heading_path = models.CharField(max_length=500, blank=True)
    text = models.TextField()
    text_normalized = models.TextField()
    char_count = models.PositiveIntegerField()
    embedding = VectorField(dimensions=settings.EMBEDDING_DIM, null=True, blank=True)
    search_vector = models.GeneratedField(
        expression=SearchVector("text_normalized", config=SEARCH_CONFIG),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        ordering = ["document", "order"]
        constraints = [
            models.UniqueConstraint(fields=["document", "order"], name="uniq_chunk_order"),
        ]
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=HNSW_M,
                ef_construction=HNSW_EF_CONSTRUCTION,
                opclasses=["vector_cosine_ops"],
            ),
            GinIndex(name="chunk_search_vector_gin", fields=["search_vector"]),
        ]

    def __str__(self) -> str:
        return f"{self.document_id}#{self.order}"
