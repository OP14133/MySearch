import asyncio
from dotenv import load_dotenv
from MySearch.search.config import Config
from MySearch.search.actions.retriever import get_retrievers
from MySearch.search.skills.researcher import ResearchConductor
from MySearch.search.agent import GPTResearcher
import pprint
# Load environment variables from .env file
load_dotenv()

async def test_scrape_data_by_query():
    # Initialize the Config object
    config = Config()

    # Retrieve the retrievers based on the current configuration
    retrievers = get_retrievers({}, config)
    print("Retrievers:", retrievers)

    # 创建一个带有必要属性的模拟研究者对象
    class MockResearcher:
        def __init__(self):
            self.query = "阿里巴巴数学竞赛姜萍事件"
            self.parent_query = ""
            self.role = ""
            self.retrievers = retrievers
            self.cfg = config
            self.agent = None
            self.verbose = True
            self.websocket = None
            self.scraper_manager = None  # Mock or implement scraper manager
            self.vector_store = None  # Mock or implement vector store
            self.visited_urls = set()
            self.report_source = ""
            self.report_type = ""
            self.add_costs = None
            self.sub_queries = None
            self.scrape_data = {}
            self.content = {}

    query = "美国大选特朗普胜利"
    gpt_researcher = GPTResearcher(query,report_type="research_report")
    # researcher = MockResearcher()
    research_conductor = gpt_researcher.research_conductor
    response = await research_conductor.conduct_research()
    report_generator = gpt_researcher.report_generator
    report = await report_generator.write_report()
    print(report)
    print('response',response)
    print('research_conductor',dir(research_conductor))
    print('GPTResearcher',dir(gpt_researcher))
    # Define a sub-query to test
    # sub_query = "阿里巴巴数学竞赛姜萍事件"

    # # 遍历所有检索器
    # for retriever_class in retrievers:
    #     # 使用子查询实例化检索器
    #     retriever = retriever_class(sub_query)
    #
    #     # 使用异步线程执行搜索，最多返回10个结果
    #     search_results = await asyncio.to_thread(
    #         retriever.search, max_results=10
    #     )
    #
    #     print("\033[35mSearch results:\033[0m")
    #     pprint.pprint(search_results, indent=4, width=80)

if __name__ == "__main__":
    asyncio.run(test_scrape_data_by_query())