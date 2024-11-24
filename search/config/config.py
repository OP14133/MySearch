import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Union, Type, get_origin, get_args
from MySearch.search.retrievers.utils import get_all_retriever_names
class Config:
    def __init__(self):
        """初始化配置类."""
        load_dotenv()  # 加载 .env 文件中的环境变量
        self.llm_kwargs = {}
        self.llm_kwargs['api_key'] = os.getenv('OPENAI_API_KEY', '')
        self.llm_kwargs['base_url'] = os.getenv('OPENAI_BASE_URL', '')
        self.smart_model = os.getenv("SMART_MODEL", "")  # 默认模型
        self.fast_model = os.getenv("FAST_MODEL", "")  # 默认模型
        self.strategic_model = os.getenv("STRATEGIC_MODEL", "")  # 默认模型
        self.temperature = float(os.getenv("TEMPERATURE", 0.4))
        self.max_tokens = int(os.getenv("MAX_TOKENS", 4000))
        self.smart_token_limit = 4000
        retriever_env = os.environ.get("RETRIEVER", "tavily")
        self.retrievers = self.parse_retrievers(retriever_env)
        self.max_iterations = 5
        self.max_search_results_per_query = 2
        self.max_subtopics = 3
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "")
        self.embedding_provider = "custom"
        self.embedding_kwargs = {}
        self.agent_role = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        self.scraper = "bs"
        self.report_format = "markdown"
        self.total_words = 1000



    def parse_retrievers(self, retriever_str: str) -> List[str]:
        """Parse the retriever string into a list of retrievers and validate them."""
        retrievers = [retriever.strip()
                      for retriever in retriever_str.split(",")]
        valid_retrievers = get_all_retriever_names() or []
        invalid_retrievers = [r for r in retrievers if r not in valid_retrievers]
        if invalid_retrievers:
            raise ValueError(
                f"Invalid retriever(s) found: {', '.join(invalid_retrievers)}. "
                f"Valid options are: {', '.join(valid_retrievers)}."
            )
        return retrievers
