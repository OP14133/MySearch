from ...search.skills.search import WebSearch
import uuid
from ...search.utils.llm import get_llm
from ...search.memory import Memory
from ...search.config.config import Config

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
        websocket,
        vector_store=None,

    ):
        self.report = report
        self.headers = headers
        self.config = Config()
        self.vector_store = vector_store
        self.websocket = websocket
        self.graph = self.create_agent()

    def create_agent(self):
        """Create React Agent Graph"""
        cfg = Config()
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
            #InMemoryVectorStore是在内存中的向量数据库。
            self.vector_store = InMemoryVectorStore(self.embedding)
            self.vector_store.add_texts(documents)

        # 创建一个graph处理图，上面初始化了InMemoryVectorStore，表示可以使用的工具
        # researcher = BasicReport(
        #     query=task,
        #     report_type=report_type,
        #     report_source=report_source,
        #     source_urls=source_urls,
        #     tone=tone,
        #     config_path=config_path,
        #     websocket=websocket,
        #     headers=headers,
        #     sub_queries=None,
        #     context=None
        # )
        web_search = WebSearch(self.websocket)
        graph = create_react_agent(
            provider,
            tools=[self.search_tool(web_search)],
            checkpointer=MemorySaver()
        )
        
        return graph
    def search_tool(self,web_search) -> Tool:
        "创建一个检索研究工具"
        @tool
        async def search_info(query):
            "当你不确定某些内容时，进行Web检索以获取相关信息"
            context = await web_search.get_context_by_search(query)
            result = "\n".join(context)
            return result
            # print("Retrieved Results:")
        return search_info
    # def vector_store_tool(self, vector_store) -> Tool:
    #     """Create Vector Store Tool"""
    #     @tool
    #     def retrieve_info(query):
    #         """
    #         当你不确定某些内容时，请查看向量数据库以获取相关上下文。
    #         """
    #         retriever = vector_store.as_retriever(k=4)
    #         results = retriever.invoke(query)
    #
    #         # 调试输出
    #         print("Retrieved Results:")
    #         for idx, result in enumerate(results):
    #             print(f"Result {idx + 1}: {result}")
    #         # retriever = vector_store.as_retriever(k = 4)
    #         return retriever.invoke(query)
    #     return retrieve_info
        
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
        # documents = InMemoryVectorStore().as_retriever(k=4).invoke()
        documents = str(self.vector_store.as_retriever(k=4).invoke(str(message)))
        message1 = f"""
         你是 舆情信息Researcher，
         用户提出问题，你针对用户的问题进行了研究拆分，通过浏览器检索到了相关舆情信息，并利用这些信息给出了总结。
         已有信息：
         {documents}\n
         历史对话: {message}
        """
        inputs = {"messages": [("user", message1)]}
        response = await self.graph.ainvoke(inputs, config=self.chat_config)
        print("response::",response["messages"])
        ai_message = response["messages"][-1].content
        if websocket is not None:
            await websocket.send_json({"type": "report", "output": ai_message})
            await websocket.send_json({"type": "path", "output": "输出完毕"})

    def get_context(self):
        """返回当前chat的上下文return the current context of the chat"""
        return self.report
