## Detailed Reports

Introducing long and detailed reports, with a completely new architecture inspired by the latest [STORM](https://arxiv.org/abs/2402.14207) paper.

In this method we do the following:

1. Trigger Initial GPT Researcher report based on task
2. Generate subtopics from research summary
3. For each subtopic the headers of the subtopic report are extracted and accumulated
4. For each subtopic a report is generated making sure that any information about the headers accumulated until now are not re-generated.
5. An additional introduction section is written along with a table of contents constructed from the entire report.
6. The final report is constructed by appending these : Intro + Table of contents + Subsection reports

介绍长篇和详细报告，采用全新的架构，灵感来自最新的 STORM 论文。

在这种方法中，我们执行以下步骤：

根据任务触发初始 GPT Researcher 报告

从研究总结中生成子主题

提取并积累每个子主题报告的标题

为每个子主题生成报告，确保不会重复生成任何关于迄今为止积累的标题的信息

编写额外的引言部分，并根据整个报告构建目录

通过附加以下内容构建最终报告：引言 + 目录 + 子主题报告