import warnings
from datetime import date, datetime, timezone

from MySearch.search.utils.enum import ReportSource, ReportType, Tone
from typing import List, Dict, Any


def generate_search_queries_prompt(
    question: str,
    parent_query: str,
    report_type: str,
    max_iterations: int = 3,
    context: List[Dict[str, Any]] = [],
):
    """生成针对给定问题的搜索查询提示
    Args:
        question (str): 需要生成搜索查询提示的问题
        parent_query (str): 主问题（仅对详细报告相关）
        report_type (str): 报告类型
        max_iterations (int): 最大生成搜索查询的次数
        context (str): 为了更好地理解任务的上下文信息

    Returns: str: 针对给定问题的搜索查询prompt
    """

    if (
        report_type == ReportType.DetailedReport.value
        or report_type == ReportType.SubtopicReport.value
    ):
        task = f"{parent_query} - {question}"
    else:
        task = question

    context_prompt = f"""
你是一位经验丰富的研究助手，负责生成针对复杂事件的搜索查询，以深入理解以下研究任务 "{task}".
当前已经收集到的上下文信息如下： {context}
""" if context else ""

    dynamic_example = ", ".join([f'"query {i+1}"' for i in range(max_iterations)])

    return f"""请根据给定的查询query和上下文信息进行查询重写，围绕查询意图展开深入分析，写出 {max_iterations} 个具体可检索的搜索查询，以检索与以下主题相关的舆情信息:"{task}"
{context_prompt}
要求：
- 每个搜索查询应具有明确的问题导向或检索意图；
- 查询需尽量具体，避免泛泛而谈；
- 尽可能包含关键元素：时间、地点、人物、事件细节等；
- 使用自然语言描述，不要只是关键词堆砌。
假设当前日期为 {datetime.now(timezone.utc).strftime('%B %d, %Y')} （如有需要可根据时间加入时效性信息。）。
您必须以以下格式回复一个字符串列表: [{dynamic_example}].
只返回该字符串列表即可，不要附加解释说明。
"""


def generate_report_prompt(
    question: str,
    context,
    report_source: str,
    report_format="apa",
    total_words=1000,
    tone=None,
):
    """给定问题和研究摘要生成舆情分析报告提示。
    Args: question (str): 需要生成报告提示的问题
          research_summary (str): 研究摘要
    Returns: str: 针对给定问题和研究摘要的报告提示
    """

    reference_prompt = ""
    if report_source == ReportSource.Web.value:
        reference_prompt = f"""
请在信息描述中明确提及每个来源的原始网址，确保来源可信并不重复。
每个网址都应超链接：[网址 网站名](网址)
此外，您必须在总结中提到的相关网址中包含超链接：
"""
    else:
        reference_prompt = f"""
您必须在信息总结末尾写出所有使用过的文档名称，并确保不添加重复的来源，每个文档只需写一次。"
"""

    tone_prompt = f"以 {tone.value} 的语气撰写总结。" if tone else ""

    return f"""
### 舆情信息检索总结任务
任务信息：
- **查询/问题**: "{question}"
- **上下文信息**: "{context}"
- **最大返回字数**: {total_words}

#### 任务描述：
您的任务是基于给定问题与上下文信息，整理并总结与舆情相关的关键信息（如果是非舆情相关问题可自行总结角度）。总结应结构化且全面，参考以下方面（严格按照上下文存在的角度总结，如上下文中缺少某些方面的信息，可忽略不写）：

1. **事件详情**：
   - 核心事件：描述事件的主要内容，包括时间、地点、相关方以及主要争议点。。
   - 起因背景：阐明事件的起因、历史背景或相关上下文。
   - 发展概述：事件的关键阶段或重要节点，形成逻辑清晰的事件发展线索
2. **最新动态**：
   - 当前状态：事件是否仍在发展？如果是，最新的更新是什么？
3. **社会反映**：
   - 公众观点：公众对该事件的主要观点是什么？是否呈现多样化或分化？
   - 官方回应：相关主体（如政府、公司、当事人）是否做出回应？如果有，具体内容和公众反应如何？
   - 媒体态度：主流媒体对事件的报道态度？
4. **潜在影响**：
   - 社会影响：该事件对社会稳定、公众舆论或文化趋势的影响。
   - 相关方影响：对事件涉及的个人、品牌或机构的声誉、经济、法律风险等可能后果。
   - 行业或领域影响：是否引发对相关行业或政策的广泛讨论或改变？
5. **后续影响**：
   - 未来趋势：舆情可能的走向及对关键相关方的持续影响。
   - 风险评估：是否存在舆情升级的可能性？潜在风险点有哪些？


#### 输出要求：
- {reference_prompt}
- 内容应根据上下文中提供的信息严格撰写，不添加虚构或未经验证的信息。
- 必须使用markdown语法
- 必须优先考虑您使用的来源的相关性、可靠性和重要性。选择可信来源。
- 使用文内引用，并在引用的句子或段落的末尾放置markdown超链接，例如：([文内引用](网址))。
- 在信息描述末尾添加参考列表及完整的URL链接，而不是超链接。
- {tone_prompt}

假设当前日期为 {date.today()}。"""


def generate_resource_report_prompt(
    question, context, report_source: str, report_format="apa", tone=None, total_words=1000
):
    """生成针对给定问题和研究摘要的资源报告提示。

    Args:
        question (str): 需要生成资源报告提示的问题。
        context (str): 研究摘要。
    Returns:
        str: 针对给定问题和研究摘要的资源报告提示。
    """

    reference_prompt = ""
    if report_source == ReportSource.Web.value:
        reference_prompt = f"""
            您必须包含所有相关的源网址。
            每个网址都应超链接：[网址 网站名](网址)
            """
    else:
        reference_prompt = f"""
            您必须在报告末尾写出所有使用过的文档名称，并确保不添加重复的来源，每个文档只需写一次。"
        """

    return (
        f'"""{context}"""\n\n基于以上信息，为以下问题或主题生成一个书目推荐报告：“{question}”。报告应详细分析每个推荐资源，'
        f'解释每个来源如何有助于找到研究问题的答案。\n'
        '重点关注每个来源的相关性、可靠性和重要性。\n'
        '确保报告结构良好，信息丰富，深入，并遵循Markdown语法。\n'
        f'报告应至少{total_words}字。\n'
        '您必须包含所有相关的源网址。\n'
        '每个网址都应超链接：[网址 网站名](网址)\n'
        f'{reference_prompt}'
    )


def generate_custom_report_prompt(
    query_prompt, context, report_source: str, report_format="apa", tone=None, total_words=1000
):
    return f'"{context}"\n\n{query_prompt}'


def generate_outline_report_prompt(
    question, context, report_source: str, report_format="apa", tone=None, total_words=1000
):
    """为给定问题和研究摘要生成大纲报告提示。
    参数：
        question (str): 需要生成大纲报告提示的问题
        context (str): 研究摘要
    返回：str: 针对给定问题和研究摘要的大纲报告提示
    """

    return (
        f'"""{context}""" 根据以上信息，为以下问题生成研究报告的大纲，使用Markdown语法：'
        f'"{question}"。大纲应提供研究报告的良好结构框架，包括主要部分、子部分和要涵盖的关键点。'
        f' 研究报告应详细、信息丰富、深入，至少包含{total_words}字。'
        ' 使用适当的Markdown语法来格式化大纲，确保可读性。'
    )


def get_report_by_type(report_type: str):
    report_type_mapping = {
        ReportType.ResearchReport.value: generate_report_prompt,
        ReportType.ResourceReport.value: generate_resource_report_prompt,
        ReportType.OutlineReport.value: generate_outline_report_prompt,
        ReportType.CustomReport.value: generate_custom_report_prompt,
        ReportType.SubtopicReport.value: generate_subtopic_report_prompt,
        ReportType.SummeryReport.value: generate_summery_report_prompt,
        ReportType.TimeLineReport.value: generate_timeline_report_prompt,
        ReportType.InfluenceReport.value: generate_influence_report_reprot_prompt,
        ReportType.SocialMediaReport.value: generate_social_media_report_prompt()
    }
    return report_type_mapping[report_type]


def auto_agent_instructions():
    return """
此任务涉及研究给定主题，无论其复杂性或是否有明确答案。研究由特定服务器进行，该服务器根据其类型和角色定义，每个服务器需要不同的指令。
代理
服务器的选择取决于主题的领域和可用于研究该主题的特定服务器名称。代理按其专业领域进行分类，每种服务器类型都与相应的表情符号相关联。

示例：
任务: "我应该投资苹果股票吗？"
回应: 
{
    "server": "💰 财务代理",
    "agent_role_prompt": "你是一位经验丰富的财务分析AI助手。你的主要目标是根据提供的数据和趋势撰写全面、深刻、公正且结构合理的财务报告。"
}
任务: "转售运动鞋会变得有利可图吗？"
回应: 
{ 
    "server": "📈 商业分析代理",
    "agent_role_prompt": "你是一位经验丰富的AI商业分析助手。你的主要目标是根据提供的商业数据、市场趋势和战略分析撰写全面、深入、公正且系统结构良好的商业报告。"
}
任务: "特拉维夫最有趣的地方有哪些？"
回应:
{
    "server": "🌍 旅游代理",
    "agent_role_prompt": "你是一位游历世界的AI导游助手。你的主要任务是撰写关于给定地点的引人入胜、深入人心、公正且结构良好的旅行报告，包括历史、景点和文化见解。"
}
"""



def generate_summary_prompt(query, data):
    """为给定问题和文本生成摘要提示。
    参数：
        query (str): 需要生成摘要提示的问题
        data (str): 用于生成摘要提示的文本
    返回：str: 针对给定问题和文本的摘要提示
    """

    return (
        f'{data}\n 根据以上文本，总结以下任务或查询："{query}"。\n 如果无法使用文本回答该查询，你必须简要总结文本。\n 包含所有事实信息，如数字、统计数据、引用等（如可用）。'
    )


################################################################################################

# DETAILED REPORT PROMPTS


def generate_subtopics_prompt() -> str:
    return """
提供主要主题：

{task}

以及研究数据：

{data}

- 构建一个子主题列表，这些子主题将作为要生成的舆情信息检索总结文档的标题。
- 这些是可能的子主题：{subtopics}。
- 不得有重复的子主题。
- 将子主题的数量限制为最多 {max_subtopics} 个。
- 最后，将子主题按任务进行排序，形成一个相关且有意义的顺序，以便在详细总结中呈现。

"重要！":
- 每个子主题必须仅与主要主题和提供的研究数据相关！

{format_instructions}
"""


def generate_subtopic_report_prompt(
        current_subtopic,
        existing_headers: list,
        relevant_written_contents: list,
        main_topic: str,
        context,
        report_format: str = "apa",
        max_subsections=5,
        total_words=800,
        tone: Tone = Tone.Objective,
) -> str:
    return f"""
上下文：
“{context}”

主题和子主题：
使用最新的信息，构建关于子主题：{current_subtopic} 的详细总结，主要主题为：{main_topic}。
您必须将子部分的数量限制为最多 {max_subsections} 个。

内容重点：
- 报告应集中回答问题，结构良好，信息丰富，深入，必要时包含事实和数字。
- 使用 markdown 语法并遵循 {report_format.upper()} 格式。

重要：内容和部分的独特性：
- 这部分指令对于确保内容的独特性和不与现有总结重叠至关重要。
- 在撰写任何新子部分之前，请仔细审查下面提供的现有标题和现有书面内容。
- 防止任何内容与现有书面内容重复。
- 不要使用任何现有标题作为新子部分的标题。
- 不要重复现有书面内容中已经覆盖的信息或其密切相关的变体，以避免重复。
- 如果您有嵌套子部分，请确保它们是独特的，并且没有在现有书面内容中覆盖。
- 确保您的内容完全是新的，不与之前子主题报告中覆盖的任何信息重叠。

“现有子主题总结”：
- 现有子主题总结及其部分标题：

    {existing_headers}

- 来自先前子主题总结的现有书面内容：

    {relevant_written_contents}

“结构和格式”：
- 由于此子总结将成为更大总结的一部分，因此只包括主要内容，分为适当的子主题，不包括任何引言或结论部分。

- 您必须在总结中包含与所引用的源 URL 相关的 markdown 超链接，例如：

    ### 部分标题

    这是示例文本。 ([url website](url))

- 使用 H2 作为主要子主题标题 (##) 和 H3 作为子部分标题 (###)。
- 对于内容结构，使用较小的 Markdown 标头（例如 H2 或 H3），避免使用最大的标题（H1），因为它将用于更大总结的标题。
- 将内容组织成不同的部分，互为补充，但不与现有总结重叠。
- 在总结中添加相似或相同的子部分时，应清楚说明新内容与现有书面内容之间的差异。例如：

    ### 新标题（与现有标题相似）

    虽然上一部分讨论了 [主题 A]，但本部分将探讨 [主题 B]。

“日期”：
如有需要，假设当前日期为 {datetime.now(timezone.utc).strftime('%B %d, %Y')}。

“重要！”：
- 重点必须放在主要主题上！您必须省略与之无关的信息！
- 不得有引言、结论、总结或参考部分。
- 必须在相关句子中包含 markdown 语法的超链接 ([url website](url))。
- 如果您在报告中添加相似或相同的子部分，必须提及现有内容与新内容之间的区别。
- 报告应至少有 {total_words} 字。
- 在整个总结中使用 {tone.value} 语气。

请勿添加结论部分。
"""


def generate_summery_report_prompt(
        current_topic,
        context,
        relevant_written_contents: dict=None,
        report_source=str,
        total_words=2000,
        report_format="apa",
        tone: Tone = Tone.Objective,
) -> str:
    return f"""
上下文：
“{context}”

主题：
使用当前获取和清理的舆情新闻数据，撰写关于主题 “{current_topic}” 的详细概述。

内容重点：
- 报告应聚焦于该主题的核心问题，包括背景信息、关键事件、影响、相关数据和事实。
- 确保结构清晰、语言准确、信息丰富，并在需要时提供事实和数据支持。
- 使用 Markdown 语法，字数不超过 {total_words}。

重要指令：
- 确保内容不与现有总结重复，尤其是以下现有书面内容：

    {relevant_written_contents}

- 强调信息的独特性和全面性，避免与现有内容的任何形式的重叠。
- 报告应采用客观语气 ({tone.value})，确保准确和中立。

“结构和格式”：
- 将内容组织成不同的子主题，用 H2 (##) 作为主要标题，H3 (###) 用于次级标题。
- 不要包括引言、结论或参考部分，因为报告将嵌入更大的总结中。
- 在相关内容中嵌入 Markdown 超链接，例如 ([source website](url))。
- 在报告中涵盖所有重要细节，但必须围绕当前主题展开，避免无关内容。

示例结构：
1. 主题背景与关键事件
2. 涉及的主要参与者或机构
3. 舆情的影响与潜在发展
4. 事件相关数据与趋势分析
5. 当前最新动态

日期：
假设当前日期为 {datetime.now(timezone.utc).strftime('%B %d, %Y')}。

注意事项：
- 子主题和段落内容需独特，不得重复先前报告中已有的内容或观点。
- 字数需达到或超过 {total_words} 字。
请严格遵循以上指令撰写报告。
"""


def generate_timeline_report_prompt(query, context: str, report_source=str,report_format='apa', tone: Tone = Tone.Objective,total_words=1000) -> str:
    return f"""
上下文：
“{context}”

任务目标：
从提供的上下文中提取所有与时间相关的关键信息，生成清晰的时间线。  
时间线内容需关注每个事件的具体时间、标题以及详细描述，确保结构化且易于理解。
注意事项：
如果没有时间线节点信息返回空列表即可，严格根据上下文推理提取，严谨随意编造。

输出格式：
返回的时间线应为 JSON 列表，每个 JSON 对象代表一个事件，包括以下字段：
- **title**: 事件标题，简洁概括事件的核心内容。
- **description**: 该时间节点事件的详细描述，包括事件背景、相关信息及影响等。
- **date**: 时间字段，格式为 “YYYY-MM-DD HH:MM:SS”。根据上下文中的时间粒度（如仅日期或包含具体时分秒）调整输出精度。
- **url**: 新闻来源url地址
注意输出格式只包含json列表，不要增加json前缀

示例输出：
```[
    {{
        "title": "事件标题",
        "description": "事件的详细描述",
        "date": "YYYY-MM-DD HH:MM:SS",
        "url": "事件来源地址"
    }},
    {{
        "title": "事件标题",
        "description": "事件的详细描述",
        "date": "YYYY-MM-DD",
        "url": "事件来源地址"
    }}
]"""


def generate_social_media_report_prompt():
    return ""


def generate_influence_report_reprot_prompt():
    return ""


def generate_draft_titles_prompt(
    current_subtopic: str,
    main_topic: str,
    context: str,
    max_subsections: int = 5
) -> str:
    return f"""
“上下文”：
“{context}”

“主要主题和子主题”：
使用最新的信息，为关于子主题：{current_subtopic} 的详细报告构建草稿部分标题。

“任务”：
1. 为子主题报告创建一个草稿部分标题列表。
2. 每个标题应简洁且与子主题相关。
3. 标题不应过于宽泛，但应足够详细，以涵盖子主题的主要方面。
4. 使用 markdown 语法为标题，使用 H3 (###) 作为标题，因为 H1 和 H2 将用于更大报告的标题。
5. 确保标题涵盖子主题的主要方面。

“结构和格式”：
以列表格式提供草稿标题，使用 markdown 语法，例如：

### 标题 1
### 标题 2
### 标题 3

“重要！”：
- 重点必须放在主要主题上！您必须省略与之无关的信息！
- 不得有引言、结论、总结或参考部分。
- 仅专注于创建标题，而不是内容。
"""


def generate_report_introduction(question: str, research_summary: str = "") -> str:
    return f"""{research_summary}\n 
根据上述最新信息，准备一份关于主题 -- {question} 的详细报告引言。
- 引言应简明扼要，结构良好，信息丰富，并使用 markdown 语法。
- 由于此引言将成为更大报告的一部分，因此请勿包含报告中通常存在的其他部分。
- 引言前应有一个 H1 标题，适合整个报告的主题。
- 必须在相关句子中包含 markdown 语法的超链接 ([url website](url))。
如有需要，假设当前日期为 {datetime.now(timezone.utc).strftime('%B %d, %Y')}。
"""

def generate_report_conclusion(query: str, report_content: str) -> str:
    """
    生成简洁的结论，总结研究报告的主要发现和意义。

    参数：
        report_content (str): 研究报告的内容。

    返回：
        str: 总结报告主要发现和意义的简洁结论。
    """
    prompt = f"""
    根据以下研究报告和研究任务，请撰写一个简洁的结论，总结主要发现及其意义：

    研究任务：{query}

    研究报告：{report_content}

    您的结论应：
    1. 回顾研究的主要观点
    2. 突出最重要的发现
    3. 讨论任何影响或后续步骤
    4. 大约 2-3 段长

    如果报告的末尾没有写“## 结论”部分标题，请在您的结论顶部添加它。
    您必须在相关句子中包含 markdown 语法的超链接 ([url website](url))。

    写下结论：
    """

    return prompt



report_type_mapping = {
    ReportType.ResearchReport.value: generate_report_prompt,
    ReportType.ResourceReport.value: generate_resource_report_prompt,
    ReportType.OutlineReport.value: generate_outline_report_prompt,
    ReportType.CustomReport.value: generate_custom_report_prompt,
    ReportType.SubtopicReport.value: generate_subtopic_report_prompt,

    ReportType.SummeryReport.value: generate_summery_report_prompt,
    ReportType.TimeLineReport.value: generate_timeline_report_prompt,
    ReportType.SocialMediaReport.value: generate_social_media_report_prompt,
    ReportType.InfluenceReport.value: generate_influence_report_reprot_prompt,

}


def get_prompt_by_report_type(report_type):
    prompt_by_type = report_type_mapping.get(report_type)
    default_report_type = ReportType.ResearchReport.value
    if not prompt_by_type:
        warnings.warn(
            f"无效的报告类型：{report_type}。\n"
            f"请使用以下之一：{', '.join([enum_value for enum_value in report_type_mapping.keys()])}\n"
            f"将使用默认报告类型：{default_report_type} 的提示。",
            UserWarning,
        )
        prompt_by_type = report_type_mapping.get(default_report_type)
    return prompt_by_type


def curate_sources(query, sources, max_results=10):
    return f"""您的目标是评估并整理提供的抓取内容，以支持研究任务：“{query}”，
    同时优先包含相关和高质量的信息，尤其是包含统计数据、数字或具体数据的来源。

最终整理的列表将作为创建研究报告的背景，因此请优先考虑：
- 尽量保留原始信息，特别是包含定量数据或独特见解的来源
- 包括广泛的视角和见解
- 仅排除明显不相关或不可用的内容

评估准则：
1. 基于以下标准评估每个来源：
   - **相关性**：包含与研究查询直接或间接相关的来源，尽量包含相关的内容。
   - **可信度**：优先选择权威来源，但如果其他来源没有明显的不可信之处也可以保留。
   - **时效性**：优先考虑最新的信息，除非较旧的数据具有重要性或价值。
   - **客观性**：如果来源提供独特或互补的视角，可以保留带有偏见的内容。
   - **定量价值**：优先考虑包含统计数据、数字或其他具体数据的来源。

2. 来源选择：
   - 包含尽可能多的相关来源，最多为{max_results}，重点考虑广泛的覆盖面和多样性。
   - 优先考虑包含统计数据、数字或可验证事实的来源。
   - 如果内容重叠且能增加深度，特别是涉及数据时，重叠内容是可以接受的。
   - 仅在来源完全不相关、严重过时或由于内容质量差无法使用时才排除。

3. 内容保留：
   - **不要**重写、总结或压缩任何来源内容。
   - 保留所有可用信息，只清除明显的垃圾或格式问题。
   - 如果某些来源包含有价值的数据或见解，尽管它们的相关性较低或不完整，仍然保留。

待评估的来源列表：
{sources}

您必须以与原始来源完全相同的 JSON 列表格式返回您的响应。
响应中**不能**包含任何 markdown 格式或附加文本（如 ```json），只能是 JSON 列表！
"""
