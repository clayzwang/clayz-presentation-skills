# PPT v3.5 Copy 层合同

遵循[阶段文件交接](../../../packages/contracts/stage-file-handoff.zh-CN.md)。读取完整研究文件，先保存完整读者讲述，再从真实讲述编辑出分页文案；不得把页面表作为首次写作入口或将分页稿串接冒充前置稿。

Copy专业输入和交接只含本阶段需求及内容文件引用。Supervisor单独保存技术运行包，供现有原生校验和报告使用。

先用files-account登记实际讲述文件。随后content.json绑定account_record，并保存slides、unit_sources、semantic_review。每页有slide_id、copy_units和既有content_relationships。文字单元按需使用title、subtitle、heading、body、annotation；heading显式使用实际正整数层级，没有默认一级或默认标题数量。

unit_sources逐项给出真实讲述字符范围start/end、verbatim/edited/derived及必要改写理由。正文可以保持完整段落，不因文字追溯而变成独立视觉块。关系说明依据实际含义，不能由标签/数组次序反推，不能用统一声明替代逐页阅读。

不生成栏数、版式、视觉分组树、强制换行或对象边界。Art依据完整故事独立设计，仍保留真实含义及有依据的变更。沿用现有fresh标题/正文读者、合并返工与原读者复看，不新增审批层。
