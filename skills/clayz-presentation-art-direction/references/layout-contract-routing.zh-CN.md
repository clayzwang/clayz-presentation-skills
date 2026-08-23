# Layout Contract 路由

Layout Contract 选择属于 Art Direction。请求必须来自已经批准的页面角色、语义
关系、用途标签、locale 与 rights context；只能选择检索回执中实际出现、已登记、
人工准入且允许物化的记录。

每个合同槽位都必须绑定任务级 Semantic Layout Tree 节点 ID 与已批准的 `copy_id`。
绑定过程不得改写文案、发明节点，也不得混入 Theme、Visual Variant、渲染器、资产或
坐标数据。

没有合格合同时，记录 `unresolved`，并使用核心 Semantic Layout Tree 流程继续，
但不得声称使用了某个命名合同。多个合同同时匹配时必须显式给出首选记录 ID，不能
静默选择相似版式。

schema、编译流程与公开资产边界见 `../../../docs/layout-contracts.zh-CN.md`。
