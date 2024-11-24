from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from ..utils import get_relevant_images, extract_title

class WebBaseLoaderScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session or requests.Session()

    def scrape(self) -> tuple:
        """
        这个 Python 函数使用 WebBaseLoader 对象从网页抓取内容，并返回连接后的页面内容。

返回值：
scrape 方法返回一个名为 content 的字符串变量，该变量包含由 WebBaseLoader 加载的文档的连接页面内容。如果在过程中发生异常，将打印错误消息并返回一个空字符串。
        """
        try:
            from langchain_community.document_loaders import WebBaseLoader
            loader = WebBaseLoader(self.link)
            loader.requests_kwargs = {"verify": False}
            docs = loader.load()
            content = ""

            for doc in docs:
                content += doc.page_content

            response = self.session.get(self.link)
            soup = BeautifulSoup(response.content, 'html.parser')
            image_urls = get_relevant_images(soup, self.link)
            
            # Extract the title using the utility function
            title = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""
