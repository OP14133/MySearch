from bs4 import BeautifulSoup
from urllib.parse import urljoin
import chardet
from ..utils import get_relevant_images, extract_title

class BeautifulSoupScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self):
        """
        This function scrapes content from a webpage by making a GET request, parsing the HTML using
        BeautifulSoup, and extracting script and style elements before returning the cleaned content.
        
        Returns:
          scrape 方法返回通过 self.link 属性指定的网页的清理和提取后的内容。该方法获取网页内容，移除脚本和样式标签，提取文本内容，并返回清理后的内容作为字符串。如果在过程中发生任何异常，将打印错误消息并返回一个空字符串。
        """
        try:
            response = self.session.get(self.link, timeout=4)

            detected_encoding = chardet.detect(response.content)['encoding']
            response.encoding = detected_encoding if detected_encoding else response.apparent_encoding
            soup = BeautifulSoup(
                response.content, "lxml", from_encoding=response.encoding
            )

            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            raw_content = self.get_content_from_url(soup)
            lines = (line.strip() for line in raw_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = "\n".join(chunk for chunk in chunks if chunk)

            image_urls = get_relevant_images(soup, self.link)
            
            # Extract the title using the utility function
            title = extract_title(soup)

            return content, image_urls, title

        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""

    def get_content_from_url(self, soup: BeautifulSoup) -> str:
        """Get the relevant text from the soup with improved filtering"""
        text_elements = []
        tags = ["h1", "h2", "h3", "h4", "h5", "p", "li", "div", "span"]

        for element in soup.find_all(tags):
            # Skip empty elements
            if not element.text.strip():
                continue

            # Skip elements with very short text (likely buttons or links)
            if len(element.text.split()) < 3:
                continue

            # Check if the element is likely to be navigation or a menu
            parent_classes = element.parent.get('class', [])
            if any(cls in ['nav', 'menu', 'sidebar', 'footer'] for cls in parent_classes):
                continue

            # Remove excess whitespace and join lines
            cleaned_text = ' '.join(element.text.split())

            # Add the cleaned text to our list of elements
            text_elements.append(cleaned_text)

        # Join all text elements with newlines
        return '\n\n'.join(text_elements)
