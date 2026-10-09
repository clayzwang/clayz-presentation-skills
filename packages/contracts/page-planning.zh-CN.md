# Copy 内容关系与 Art 逐页艺术规划 — v0.19.0

新任务使用内容包 **3.4**、Art 计划 **2.3**。3.3 与 Art 2.1／2.2
继续按历史合同回读，不给旧证据改版本或补写当时不存在的规划。

## Copy 交代语义关系

说明每段正文解释或支撑什么：归属于某个标题、共同支撑多个标题，
或者没有局部标题归属而承担全页用途。未声明是未知，不能当成无归属。
标题之间是并列、步骤、条件还是其他关系，也要按内容说明；同级标题
和文案数组顺序不能代替实际关系。

在每页的 `content_relationships` 中单独记录，文字单元的五类角色不变：

```json
{
  "heading_relationships": "H1是入口动作，H2与H3说明两项支持职责；来源未确定两项职责之间的严格先后。",
  "body_relations": [
    {"copy_id":"B1","heading_ids":["H2"],"purpose":"解释第二项职责的作用，同时支撑全页判断。"},
    {"copy_id":"B2","heading_ids":["H2","H3"],"purpose":"说明两项职责共同遵循的条件。"},
    {"copy_id":"B3","heading_ids":[],"purpose":"限定整页证据，没有局部标题归属。"}
  ]
}
```

这是合成关系示例，不是版式模板。每个 `body` ID 恰好覆盖一次。
`heading_ids` 必须明确给出一个、多个本页标题 ID，或者 `[]`；
`purpose` 用自然语言说明用途。必要时也可记录 annotation 的关系。
没有正文可以使用 `body_relations:[]`；没有局部标题时，在
`heading_relationships` 中明确说明。一个标题可以同时拥有直属正文和
子标题；在 `heading_relationships` 中说明子标题关系，将直属正文的
`heading_ids` 指向该上级标题。正文可以归属于任一级标题，无须只归属
最末一级。Art 决定这种混合层级的视觉组织。不要求每个标题都有正文，也不让
这些关系约束 Art 的原生对象、容器、样式、空间阅读顺序或形状边界。

## Art 先统筹页面，再细化对象

阅读全稿及内容关系，说明本页核心判断、现有内容组、正文的不同作用，
再选择整体构图、阅读动线、层级和空间分量。交代重要元素如何处理：
哪里简洁、哪里展开、哪些属于一组、什么需要突出。含义不清回 Copy，
不能用排布替内容作语义裁决。

判断序号、标签、概括标题、重点突出、slogan 等是否有帮助，记录新增
表达的用途和批准内容依据；无需增加也是有效判断。允许 Art 在忠实于
批准含义的范围内创造附加的表达性文字。既有 Copy 保持不变；替换文案
回 Copy，新增事实或实质改变关系回相应上游环节。

寻找同一元素或有机组合共同承担相互支持的表达作用的机会。例如真实
流程中，块的指向性形状、首尾衔接可以同时承载内容和方向，允许省去
独立箭头。线、字、形状、位置、颜色也可共同表达关系。以内容和可读
空间判断，不设箭头禁令、必用尖头块、等大内容组或元素数量目标。
重要的语义包含与原生编辑分组分别说明；视觉嵌套和同页 ID 本身不能
证明 PPTX 父子关系或分组。

在细化原生对象规格前，保存真实的逐页艺术规划。采用自然语言，不用
版式菜单或审美评分。规划草稿包含顺序一致的 `slides`，每页给出
`slide_id` 及以下内容：

- `page_message`：本页判断、希望观众首先理解什么；
- `content_analysis`：内容组、归属、作用、密度和已知缺口；
- `composition`：整体排布、动线、重点与选择理由；
- `element_strategy`：重要元素或组合如何服务表达；
- `addition_decision`：是否增加表达元素、原因是什么；
- `expression_additions`：`[]` 或包含 `text`、`purpose`、有效本页
  `source_copy_ids` 的新增表达清单。

这些字段记录可交接的设计决策及依据，不要求披露私有推理过程。
没有字数配额或规定版式能替代专业判断。

```bash
python scripts/stage_documents.py record-planning --package copy-package.json \
  --plan page-planning-draft.json --output page-planning-r1.json
```

命令校验 Copy、绑定准确的 Copy 哈希和包身份，写入实际记录时间，
拒绝覆盖旧记录。随后制作图片稿与对象规格，检查实际彩色页面和整稿
顺序；必要修正在新的不可变版本中保存，再锁定批准设计：

```bash
python scripts/stage_documents.py lock-design --package copy-package.json \
  --plan art-plan-draft.json --planning page-planning-r1.json \
  --output art-plan-approved.json
```

Art 2.3 的 `page_planning` 保存原文件绝对路径、SHA-256、字节数，
以及准确 base64 字节和解码后的 `content`，用于离开原文件系统后的
回读。规划记录时间必须早于设计锁定。这能证明记录顺序，不能证明
私有思考顺序，也不能独立证明此前从未探索对象。不能看到最终 PPTX
后补写缺失的设计前证据。Output 同时阅读规划、全稿图片和对应规格，
保留 Art 的锁定基准。

## 审计规划及实际实现

沿用 Supervisor、Independent Auditor、观察记录和交付政策，不增加
第六阶段或审美审批门槛。每页 `design_comparison.slides` 增加四项观察：

- `page_planning`：真实页面规划、记录顺序与证据局限；
- `content_relationships`：是否忠实表达 Copy 的归属与关系；
- `expression_additions`：新增表达是否有效、有依据且未新增主张；
- `planned_realization`：规格、图片稿与成品是否实现预期理解、可读性
  和实际注意顺序。

每项使用 `status:pass|fail|uncertain` 和具体 `observation`。缺失或
未检查的证据记录为 uncertain，明确缺口，不能伪造 pass。fail／uncertain
须对应报告 issue IDs，并标明最早负责环节（logic、copy、art-direction 或
output）；有这些发现的报告不能标成 clean。成品渲染延后仍检查已有
规划，实际呈现保持 uncertain。独立审计发现原样保留。

字段齐全、理由文字、对象数量、执行保真都不能证明艺术质量。检查
实际页面中的分组、层级、动线是否成立；含义歧义回 Copy，构图问题回
Art，制作偏离回 Output。真实规划字节和派生的可读规划进入既有阶段
文档及交接 ZIP；原文件路径失效后，报告仍应能核验这些证据。
