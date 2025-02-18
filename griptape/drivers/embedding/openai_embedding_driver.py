from __future__ import annotations
import os
from typing import Optional
import openai
from attr import define, field, Factory
from griptape.drivers import BaseEmbeddingDriver
from griptape.tokenizers import OpenAiTokenizer


@define
class OpenAiEmbeddingDriver(BaseEmbeddingDriver):
    """
    Attributes:
        api_type: Can be changed to use OpenAI models on Azure.
        api_version: API version.
        api_base: API URL.
        api_key: API key to pass directly; by default uses `OPENAI_API_KEY_PATH` environment variable.
        dimensions: Vector dimensions. Defaults to `1536`.
        model: OpenAI embedding model name. Uses `text-embedding-ada-002` by default.
        organization: OpenAI organization.
        tokenizer: Custom `OpenAiTokenizer`.
        user: OpenAI user.
    """

    DEFAULT_MODEL = "text-embedding-ada-002"
    DEFAULT_DIMENSIONS = 1536

    model: str = field(default=DEFAULT_MODEL, kw_only=True)
    dimensions: int = field(default=DEFAULT_DIMENSIONS, kw_only=True)
    api_type: str = field(default=openai.api_type, kw_only=True)
    api_version: Optional[str] = field(default=openai.api_version, kw_only=True)
    api_base: str = field(default=openai.api_base, kw_only=True)
    api_key: Optional[str] = field(
        default=Factory(lambda: os.environ.get("OPENAI_API_KEY")), kw_only=True
    )
    organization: Optional[str] = field(
        default=openai.organization, kw_only=True
    )
    tokenizer: OpenAiTokenizer = field(
        default=Factory(
            lambda self: OpenAiTokenizer(model=self.model), takes_self=True
        ),
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        openai.api_type = self.api_type
        openai.api_version = self.api_version
        openai.api_base = self.api_base
        openai.api_key = self.api_key
        openai.organization = self.organization

    def try_embed_chunk(self, chunk: str) -> list[float]:
        # Address a performance issue in older ada models
        # https://github.com/openai/openai-python/issues/418#issuecomment-1525939500
        if self.model.endswith("001"):
            chunk = chunk.replace("\n", " ")
        return openai.Embedding.create(**self._params(chunk))["data"][0][
            "embedding"
        ]

    def _params(self, chunk: str) -> dict:
        return {
            "input": chunk,
            "model": self.model,
            "api_key": self.api_key,
            "organization": self.organization,
            "api_version": self.api_version,
            "api_base": self.api_base,
            "api_type": self.api_type,
        }
