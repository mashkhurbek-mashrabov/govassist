"""Tests for embedding port: FakeEmbedder determinism and GeminiEmbedder with a mock client."""

import math
from unittest.mock import AsyncMock, MagicMock

import pytest
from django.test import override_settings

from apps.corpus.embeddings import (
    DOCUMENT_TEMPLATE,
    QUERY_TEMPLATE,
    DocumentInput,
    FakeEmbedder,
    GeminiEmbedder,
    format_document,
)

SAMPLE_DIM = 32


# ---------------------------------------------------------------------------
# format_document
# ---------------------------------------------------------------------------


class TestFormatDocument:
    """Tests for ``format_document``."""

    def test_with_heading_path(self) -> None:
        """Title and heading path are joined with `` › ``."""
        item = DocumentInput(title="NAMUNA Title", heading_path="2-bob › 3-modda", text="body")
        result = format_document(item)
        assert result == DOCUMENT_TEMPLATE.format(
            title="NAMUNA Title › 2-bob › 3-modda", text="body"
        )

    def test_without_heading_path(self) -> None:
        """When heading path is empty, only title is used."""
        item = DocumentInput(title="NAMUNA Title", heading_path="", text="body")
        result = format_document(item)
        assert result == DOCUMENT_TEMPLATE.format(title="NAMUNA Title", text="body")

    def test_empty_title_and_path(self) -> None:
        """When both title and heading path are empty, ``none`` is used."""
        item = DocumentInput(title="", heading_path="", text="body")
        result = format_document(item)
        assert result == DOCUMENT_TEMPLATE.format(title="none", text="body")

    def test_empty_title_with_path(self) -> None:
        """When title is empty but heading path is set, only heading path is used."""
        item = DocumentInput(title="", heading_path="2-bob", text="body text")
        result = format_document(item)
        assert result == DOCUMENT_TEMPLATE.format(title="2-bob", text="body text")


# ---------------------------------------------------------------------------
# FakeEmbedder
# ---------------------------------------------------------------------------


class TestFakeEmbedder:
    """Tests for ``FakeEmbedder``."""

    @pytest.fixture
    def embedder(self) -> FakeEmbedder:
        """A fake embedder with a small dimension for fast tests."""
        return FakeEmbedder(dimensions=SAMPLE_DIM)

    @pytest.mark.asyncio
    async def test_deterministic(self, embedder: FakeEmbedder) -> None:
        """Same text produces the same vector twice."""
        item = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA davlat xizmati")
        v1 = (await embedder.embed_documents([item]))[0]
        v2 = (await embedder.embed_documents([item]))[0]
        assert v1 == v2

    @pytest.mark.asyncio
    async def test_normalized(self, embedder: FakeEmbedder) -> None:
        """Output vectors are L2-normalized (magnitude ≈ 1.0)."""
        item = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA test normalization")
        vector = (await embedder.embed_documents([item]))[0]
        magnitude = math.sqrt(sum(v * v for v in vector))
        assert abs(magnitude - 1.0) < 1e-6

    @pytest.mark.asyncio
    async def test_similar_texts_higher_similarity(self, embedder: FakeEmbedder) -> None:
        """Texts that share words produce more similar vectors than unrelated texts."""
        item_a = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA davlat xizmati hujjat")
        item_b = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA davlat xizmati parol")
        item_c = DocumentInput(
            title="SAMPLE", heading_path="", text="NAMUNA kompyuter dasturlash boshqa"
        )
        va = (await embedder.embed_documents([item_a]))[0]
        vb = (await embedder.embed_documents([item_b]))[0]
        vc = (await embedder.embed_documents([item_c]))[0]
        sim_ab = sum(a * b for a, b in zip(va, vb, strict=True))
        sim_ac = sum(a * c for a, c in zip(va, vc, strict=True))
        assert sim_ab > sim_ac

    @pytest.mark.asyncio
    async def test_vector_dimension(self, embedder: FakeEmbedder) -> None:
        """Output vector has the configured dimension."""
        item = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA test")
        vector = (await embedder.embed_documents([item]))[0]
        assert len(vector) == SAMPLE_DIM

    @pytest.mark.asyncio
    async def test_embed_query(self, embedder: FakeEmbedder) -> None:
        """``embed_query`` returns a vector of the correct dimension."""
        vector = await embedder.embed_query("NAMUNA sample query")
        assert len(vector) == SAMPLE_DIM


# ---------------------------------------------------------------------------
# GeminiEmbedder (with fake client)
# ---------------------------------------------------------------------------


class TestGeminiEmbedder:
    """Tests for ``GeminiEmbedder`` using a mock client."""

    @pytest.fixture
    def fake_embedding(self) -> list[float]:
        """A SAMPLE embedding vector of the right shape."""
        return [0.1] * SAMPLE_DIM

    @pytest.fixture
    def mock_client(self, fake_embedding: list[float]) -> MagicMock:
        """A mock ``genai.Client`` whose ``aio.models.embed_content`` is an AsyncMock."""
        client = MagicMock()
        embedding_obj = MagicMock()
        embedding_obj.values = fake_embedding
        response = MagicMock()
        response.embeddings = [embedding_obj]
        client.aio.models.embed_content = AsyncMock(return_value=response)
        return client

    @pytest.fixture
    def embedder(self, mock_client: MagicMock) -> GeminiEmbedder:
        """A ``GeminiEmbedder`` using the mock client."""
        return GeminiEmbedder(
            client=mock_client,
            model="fake-model-SAMPLE",
            dimensions=SAMPLE_DIM,
            concurrency=1,
            max_tries=1,
        )

    @pytest.mark.asyncio
    async def test_embed_documents_one_call_per_text(
        self, embedder: GeminiEmbedder, mock_client: MagicMock
    ) -> None:
        """Each document item triggers exactly one ``embed_content`` call."""
        items = [
            DocumentInput(title="SAMPLE A", heading_path="", text="NAMUNA text one"),
            DocumentInput(title="SAMPLE B", heading_path="", text="NAMUNA text two"),
        ]
        result = await embedder.embed_documents(items)
        assert len(result) == 2
        assert mock_client.aio.models.embed_content.call_count == 2

    @pytest.mark.asyncio
    async def test_output_dimensionality_passed(
        self, embedder: GeminiEmbedder, mock_client: MagicMock
    ) -> None:
        """``output_dimensionality`` is set in the config passed to the API."""
        item = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA test")
        await embedder.embed_documents([item])
        call_kwargs = mock_client.aio.models.embed_content.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
        assert config.output_dimensionality == SAMPLE_DIM

    @pytest.mark.asyncio
    async def test_query_prefix_used(
        self, embedder: GeminiEmbedder, mock_client: MagicMock
    ) -> None:
        """``embed_query`` wraps the query in the ``QUERY_TEMPLATE``."""
        query = "NAMUNA sample question"
        await embedder.embed_query(query)
        call_args = mock_client.aio.models.embed_content.call_args
        contents = call_args.kwargs.get("contents") or call_args[1].get("contents")
        assert contents == QUERY_TEMPLATE.format(query=query)

    @pytest.mark.asyncio
    async def test_empty_response_raises_value_error(self, mock_client: MagicMock) -> None:
        """An empty embedding response raises ``ValueError``."""
        empty_response = MagicMock()
        empty_response.embeddings = []
        mock_client.aio.models.embed_content = AsyncMock(return_value=empty_response)
        embedder = GeminiEmbedder(
            client=mock_client,
            model="fake-model-SAMPLE",
            dimensions=SAMPLE_DIM,
            concurrency=1,
            max_tries=1,
        )
        item = DocumentInput(title="SAMPLE", heading_path="", text="NAMUNA test")
        with pytest.raises(ValueError, match="no embedding"):
            await embedder.embed_documents([item])

    @pytest.mark.asyncio
    @override_settings(GEMINI_EMBEDDING_MODEL="fake-model-SAMPLE", EMBEDDING_DIM=SAMPLE_DIM)
    async def test_model_name_attribute(self, embedder: GeminiEmbedder) -> None:
        """``model_name`` is set from the constructor argument."""
        assert embedder.model_name == "fake-model-SAMPLE"
