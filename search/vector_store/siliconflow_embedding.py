import os
import requests
from langchain.embeddings.base import Embeddings
from pydantic import (
    BaseModel,
    ConfigDict,
    PrivateAttr,
    model_validator,
)
from httpx import AsyncClient, Client
from typing import (
    List,
    Optional,
)
class SiliconFlowEmbeddings(BaseModel, Embeddings):
    """SiliconFlow embedding model integration."""

    model: str
    """Model name to use."""

    token: str
    """API token for SiliconFlow."""

    base_url: str = "https://api.siliconflow.cn/v1/embeddings"
    """Base url for SiliconFlow embeddings API."""

    client_kwargs: Optional[dict] = {}
    """Additional kwargs to pass to the httpx Client."""

    _client: Client = PrivateAttr(default=None)
    """The client to use for making requests."""

    _async_client: AsyncClient = PrivateAttr(default=None)
    """The async client to use for making requests."""

    model_config = ConfigDict(
        extra="forbid",
    )

    @model_validator(mode="after")
    def _set_clients(self) -> "SiliconFlowEmbeddings":
        """Set clients to use for SiliconFlow."""
        client_kwargs = self.client_kwargs or {}
        self._client = Client(**client_kwargs)
        self._async_client = AsyncClient(**client_kwargs)
        return self

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        embeddings = []
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        for text in texts:
            payload = {
                "model": self.model,
                "input": [text],  # 将单个文本作为列表传入
                "encoding_format": "float"
            }
            response = self._client.post(self.base_url, json=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Error {response.status_code}: {response.text}")
            embedding = response.json().get("data", [])
            if embedding:
                embeddings.append(embedding[0]['embedding'])  # 直接添加到结果中

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        return self.embed_documents([text])[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs asynchronously, processing each text individually."""
        embeddings = []
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        for text in texts:
            payload = {
                "model": self.model,
                "input": [text],  # 将单个文本作为列表传入
                "encoding_format": "float"
            }

            # 异步请求
            response = await self._async_client.post(self.base_url, json=payload, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Error {response.status_code}")

            # 解析返回的嵌入数据
            embedding = response.json().get("data", [])
            if embedding:
                embeddings.append(embedding[0]['embedding'])  # 直接添加到结果中

        return embeddings

    async def aembed_query(self, text: str) -> List[float]:
        """Embed query text asynchronously."""
        return await self.aembed_documents([text])

# 初始化 SiliconFlow Embeddings
siliconflow_token = "sk-yavtxhioyhzqqdmxihlkaumwqyhuczpsznqnypmuyrqqymun"
embed = SiliconFlowEmbeddings(model="BAAI/bge-m3", token=siliconflow_token)

