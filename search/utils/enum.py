from enum import Enum

"""
定义了三个枚举类：ReportType、ReportSource 和 Tone。每个枚举类都包含一组预定义的常量，用于表示不同的报告类型、报告来源和语气。
"""
class ReportType(Enum):
    ResearchReport = "research_report" #研究报告
    ResourceReport = "resource_report" #资源报告
    OutlineReport = "outline_report" #大纲报告
    CustomReport = "custom_report" #自定义报告
    DetailedReport = "detailed_report" #详细报告
    SubtopicReport = "subtopic_report" #子主题报告


class ReportSource(Enum):
    Web = "web"
    Local = "local"
    LangChainDocuments = "langchain_documents"
    LangChainVectorStore = "langchain_vectorstore"
    Static = "static"
    Hybrid = "hybrid"


class Tone(Enum):
    Objective = "客观语气（公正且无偏见地呈现事实和发现）。"
    Formal = "正式语气（遵循学术标准，使用复杂的语言和结构）。"
    Analytical = (
        "分析语气（对数据和理论进行批判性评估和详细审查）。"
    )
    Persuasive = (
        "说服语气（说服观众接受某个观点或立场或论点）。"
    )
    Informative = (
        "信息语气（提供关于某个主题的清晰和全面的信息）"
    )
    Explanatory = "解释语气（澄清复杂的概念和过程）。"
    Descriptive = (
        "描述语气（详细描述现象、实验或案例研究）"
    )
    Critical = "批判语气（判断研究的效度和相关性及其结论）"
    Comparative = "比较语气（并列不同的理论、数据或方法，以突出差异和相似之处）"
    Speculative = "推测语气（探索假设和潜在的影响或未来的研究方向）"
    Reflective = "反思语气（考虑研究过程和个人见解或经验）"
    Narrative = (
        "叙事语气（通过讲故事来说明研究结果或方法）"
    )
    Humorous = "幽默语气（轻松愉快且引人入胜，通常是为了使内容更易于理解）"
    Optimistic = "乐观语气（强调积极的发现和潜在的好处）"
    Pessimistic = (
        "悲观语气（关注限制、挑战或负面结果）"
    )
