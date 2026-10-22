from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from pgvector.django import HnswIndex, VectorField

from apps.common.i18n import Lang
from apps.common.models import BaseModel, ReviewStatus

SEARCH_CONFIG = "simple"
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 64


class DocumentKind(models.TextChoices):
    """What a document is; maps to ``Source.kind`` in the contract."""

    LAW = "law", "Law"
    SERVICE_PAGE = "service_page", "Service page"
    OTHER = "other", "Other"


class Document(BaseModel):
    """A crawled page or act, reviewed by the admin before it is indexed."""

    source = models.ForeignKey(
        "collector.CrawlSource",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    kind = models.CharField(max_length=20, choices=DocumentKind, default=DocumentKind.OTHER)
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    publisher = models.CharField(max_length=100)
    language = models.CharField(max_length=8, choices=Lang, default=Lang.UZ_LATN)
    section_label = models.CharField(max_length=200, null=True, blank=True)  # noqa: DJ001
    published_at = models.DateField(null=True, blank=True)
    fetched_at = models.DateTimeField()
    text = models.TextField()
    text_hash = models.CharField(max_length=64)
    corpus_version = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=ReviewStatus, default=ReviewStatus.PENDING)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        return self.title


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
