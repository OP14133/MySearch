import re
from collections import Counter
from typing import List, Dict, Optional
import jieba
from fastapi import WebSocket
from wordcloud import WordCloud

async def generate_wordcloud_data(text: str, max_words: int = 100, websocket: Optional[WebSocket] = None,) -> List[Dict[str, int]]:
    """
    Generate word cloud data from input text, supports Chinese segmentation.

    Args:
        text (str): Input text material.
        max_words (int): Maximum number of words in the output.

    Returns:
        List[Dict[str, int]]: A list of dictionaries with word and weight.
    """
    # Preprocess text: remove special characters
    if isinstance(text, list):
        text = " ".join(text)
    clean_text = re.sub(r"[^\w\s]", "", text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # Use jieba for segmentation
    segmented_words = jieba.cut(clean_text)

    # Count word frequencies
    word_frequencies = Counter(segmented_words)
    # Remove single-character words and filter by length
    filtered_frequencies = {word: freq for word, freq in word_frequencies.items() if len(word) > 1}

    # Sort by frequency and keep the top `max_words`
    sorted_words = sorted(filtered_frequencies.items(), key=lambda x: x[1], reverse=True)[:max_words]


    # Format output as a list of dictionaries
    result = [{"word": word, "weight": freq} for word, freq in sorted_words]
    if websocket:
        try:
            # Construct the message
            message = {"type": "word_cloud", "output": result}
            # Send JSON data through WebSocket
            await websocket.send_json(message)
        except Exception as e:
            print(f"Failed to send data via WebSocket: {e}")
    return result



if __name__ == "__main__":
    # Example usage
    sample_text = """
    1月7日，被接到泰国达府的中国人王星接受当地媒体采访，表示感谢泰国政府和移民局的帮助，让他安全抵达当地。王星已经离开了达府移民局，被送往湄索机场。
    """
    wordcloud_data = generate_wordcloud_data(sample_text, max_words=10)
    print(wordcloud_data)
