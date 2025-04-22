import asyncio

from MySearch.search.agent import GPTResearcher
from MySearch.search.skills.deep_research import DeepResearchSkill
async def main():
    researcher = GPTResearcher("小米su7车祸事件")
    deepResearch = DeepResearchSkill(researcher)
    result = await deepResearch.extract_keywords_and_date_range("小米su7车祸事件")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())