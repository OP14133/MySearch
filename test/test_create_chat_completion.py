# from utils.llm import create_chat_completion
import asyncio
from dotenv import load_dotenv
import os
import sys
# from ..search.config.config import Config
load_dotenv()

print(sys.path)
# async def main():
#     cfg = Config()
#
#     # try:
#     #     report = await create_chat_completion(
#     #         model= cfg.model,
#     #         messages = [{"role": "user", "content": "你是什么模型"}],
#     #         temperature=0.35,
#     #         stream=True,
#     #         max_tokens=cfg.max_tokens,
#     #         llm_kwargs=cfg.llm_kwargs
#     #     )
#     # except Exception as e:
#     #     print(f"Error in calling LLM: {e}")
#
# # Run the async function
# asyncio.run(main())