import importlib
from typing import Any
from colorama import Fore, Style, init
import os

_SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "azure_openai",
    "cohere",
    "google_vertexai",
    "google_genai",
    "fireworks",
    "ollama",
    "together",
    "mistralai",
    "huggingface",
    "groq",
    "bedrock",
}


class GenericLLMProvider:

    def __init__(self, llm):
        self.llm = llm

    @classmethod
    def from_provider(cls, **kwargs: Any):
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(**kwargs)
        return cls(llm)


    async def get_chat_response(self, messages, stream, websocket=None, type=None):
        if not stream:
            # Getting output from the model chain using ainvoke for asynchronous invoking
            output = await self.llm.ainvoke(messages)

            return output.content

        else:
            return await self.stream_response(messages, websocket, type)

    async def stream_response(self, messages, websocket=None, type=None):
        paragraph = ""
        response = ""

        # Streaming the response using the chain astream method from langchain
        async for chunk in self.llm.astream(messages):
            content = chunk.content
            if content is not None:
                response += content
                paragraph += content
                if "\n" in paragraph:
                    if type is not None:
                        await self._send_output(paragraph, websocket, type=type)
                    else:
                        await self._send_output(paragraph, websocket)
                    paragraph = ""

        if paragraph:
            if type is not None:
                await self._send_output(paragraph, websocket, type=type)
            else:
                await self._send_output(paragraph, websocket)

        return response

    async def _send_output(self, content, websocket=None, type="report"):
        if websocket is not None:
            await websocket.send_json({"type": type, "output": content})
        else:
            print(f"{Fore.GREEN}{content}{Style.RESET_ALL}")


def _check_pkg(pkg: str) -> None:
    if not importlib.util.find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        # Import colorama and initialize it
        init(autoreset=True)
        # Use Fore.RED to color the error message
        raise ImportError(
            Fore.RED + f"Unable to import {pkg_kebab}. Please install with "
            f"`pip install -U {pkg_kebab}`"
        )
