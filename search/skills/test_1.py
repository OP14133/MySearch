import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from MySearch.search.skills.search import WebSearch


@pytest.fixture
def mock_websocket():
    """模拟 WebSocket 实例"""
    return MagicMock()


@pytest.fixture
def mock_config():
    """模拟 Config 配置对象"""
    mock_cfg = MagicMock()
    mock_cfg.retrievers = [MagicMock()]
    mock_cfg.max_search_results_per_query = 10
    return mock_cfg


@pytest.fixture
def mock_browser_manager():
    """模拟 BrowserManager"""
    mock_scraper_manager = MagicMock()
    mock_scraper_manager.browse_urls = AsyncMock(return_value=["page1", "page2", "page3"])
    return mock_scraper_manager


@pytest.fixture
def web_search_instance(mock_config, mock_browser_manager, mock_websocket):
    """创建 WebSearch 实例，并注入依赖项"""
    # 通过 mock 传入配置和浏览器管理器
    web_search = WebSearch(
        query="example query",
        websocket=mock_websocket,
        visited_urls=set()
    )
    web_search.cfg = mock_config
    web_search.scraper_manager = mock_browser_manager
    return web_search


@pytest.mark.asyncio
async def test_get_context_by_search(web_search_instance, mock_websocket):
    """测试 WebSearch 类的 __get_context_by_search 方法"""

    # 模拟 get_search_results 方法
    web_search_instance.plan_research = AsyncMock(return_value=["sub_query_1", "sub_query_2"])

    # 模拟 __process_sub_query 方法
    web_search_instance.__process_sub_query = AsyncMock(return_value="processed context")

    # 运行 WebSearch 的 __get_context_by_search 方法
    context = await web_search_instance.__get_context_by_search("example query")

    # 验证调用的次数和参数
    web_search_instance.plan_research.assert_called_once_with("example query")
    assert len(context) == 2  # 我们预计有两个子查询被处理

    # 验证日志输出
    mock_websocket.send_json.assert_any_call(
        {"type": "logs", "output": "subqueries", "data": ['sub_query_1', 'sub_query_2']})


@pytest.mark.asyncio
async def test_process_sub_query(web_search_instance, mock_websocket):
    """测试 WebSearch 类的 __process_sub_query 方法"""

    # 模拟 __scrape_data_by_query 方法
    web_search_instance.__scrape_data_by_query = AsyncMock(return_value=["scraped data 1", "scraped data 2"])

    # 模拟 get_similar_content_by_query 方法
    web_search_instance.get_similar_content_by_query = AsyncMock(return_value="similar content")

    # 测试单个子查询
    result = await web_search_instance.__process_sub_query("sub_query_1")

    # 验证
    web_search_instance.__scrape_data_by_query.assert_called_once_with("sub_query_1")
    web_search_instance.get_similar_content_by_query.assert_called_once_with("sub_query_1",
                                                                             ["scraped data 1", "scraped data 2"])

    # 确保返回的内容是压缩后的内容
    assert result == "similar content"


@pytest.mark.asyncio
async def test_scrape_data_by_query(web_search_instance):
    """测试 WebSearch 类的 __scrape_data_by_query 方法"""

    # 模拟 retriever 类的搜索行为
    mock_retriever = MagicMock()
    mock_retriever.search = AsyncMock(return_value=[{"href": "http://example.com/1"}, {"href": "http://example.com/2"}])

    web_search_instance.cfg.retrievers = [mock_retriever]

    # 执行 scrape 数据
    scraped_data = await web_search_instance.__scrape_data_by_query("sub_query_1")

    # 验证调用了正确的搜索函数
    mock_retriever.search.assert_called_once_with(max_results=10)

    # 验证返回的搜索结果
    assert len(scraped_data) == 2
    assert "http://example.com/1" in scraped_data
    assert "http://example.com/2" in scraped_data


@pytest.mark.asyncio
async def test_get_similar_content_by_query(web_search_instance):
    """测试 WebSearch 类的 get_similar_content_by_query 方法"""

    # 模拟 Memory 对象的行为
    mock_embedding = MagicMock()
    web_search_instance.cfg.embedding_provider = "embedding_provider"
    web_search_instance.cfg.embedding_model = "embedding_model"
    web_search_instance.cfg.embedding_kwargs = {}

    # 模拟 ContextCompressor 行为
    mock_compressor = MagicMock()
    mock_compressor.async_get_context = AsyncMock(return_value="compressed context")

    # 替换实际使用的 ContextCompressor
    web_search_instance.get_similar_content_by_query = mock_compressor.async_get_context

    # 执行获取相似内容
    result = await web_search_instance.get_similar_content_by_query("sub_query_1", ["scraped data 1", "scraped data 2"])

    # 验证返回的内容
    assert result == "compressed context"
    mock_compressor.async_get_context.assert_called_once_with(query="sub_query_1", max_results=10)
