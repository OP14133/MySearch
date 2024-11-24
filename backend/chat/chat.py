from fastapi import WebSocket
import uuid
from MySearch.search.utils.llm import get_llm
from MySearch.search.memory import Memory
from MySearch.search.config.config import Config

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from langchain_community.vectorstores import InMemoryVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool, tool

class ChatAgentWithMemory:
    def __init__(
        self,
        report: str,
        headers,
        vector_store = None
    ):
        self.report = report
        self.headers = headers
        self.config = Config()
        self.vector_store = vector_store
        self.graph = self.create_agent()

    def create_agent(self):
        """Create React Agent Graph"""
        cfg = Config()

        # Retrieve LLM using get_llm with settings from config
        provider = get_llm(
            model=cfg.smart_model,
            temperature=0.35,
            max_tokens=cfg.smart_token_limit,
            **self.config.llm_kwargs
        ).llm

        # 如果向量数据库没有初始化，处理文档并添加到向量数据库
        if not self.vector_store:
            documents = self._process_document(self.report)
            self.chat_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
            self.embedding = Memory(
                cfg.embedding_provider,
                cfg.embedding_model,
                **cfg.embedding_kwargs
            ).get_embeddings()
            self.vector_store = InMemoryVectorStore(self.embedding)
            self.vector_store.add_texts(documents)

        # Create the React Agent Graph with the configured provider
        graph = create_react_agent(
            provider,
            tools=[self.vector_store_tool(self.vector_store)],
            checkpointer=MemorySaver()
        )
        
        return graph
    
    def vector_store_tool(self, vector_store) -> Tool:
        """Create Vector Store Tool"""
        @tool 
        def retrieve_info(query):
            """
            当你不确定某些内容时，请查阅报告以获取相关上下文。
            """
            retriever = vector_store.as_retriever(k = 4)
            return retriever.invoke(query)
        return retrieve_info
        
    def _process_document(self, report):
        """split报告为chunk"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        documents = text_splitter.split_text(report)
        return documents

    async def chat(self, message, websocket):
        """Chat with React Agent"""
        message = f"""
         你是 舆情信息Researcher，
         
         这是一个用户和你之间的聊天消息：
         聊天内容是关于你创建的研究报告。根据给定的上下文和报告回答。
         你必须根据报告包含对你的回答的引用。
         
         Report: {self.report}
         User Message: {message}
        """
        inputs = {"messages": [("user", message)]}
        response = await self.graph.ainvoke(inputs, config=self.chat_config)
        ai_message = response["messages"][-1].content
        if websocket is not None:
            await websocket.send_json({"type": "chat", "content": ai_message})

    def get_context(self):
        """返回当前chat的上下文return the current context of the chat"""
        return self.report
