# 当前Art知识证据交接

本页解释当前代码已存在的格式，不增加质量门禁、读取数量或事后通过依据。
先真实阅读相关知识节点、完整CU及所需专业正文，再决定视觉采用；实际读过、
形成选择、作品发生变化和读者理解改善是不同观察。保留所有原返回及失败。

Art的knowledge角色使用`io.clayz.presentation.art-knowledge-evidence/1.0`。
其中`raw_returns`为当前真实节点/CU/命令返回的path、bytes、sha256数组，
`manifest`引用当前知识包原manifest。可记录version、recorded_at、navigation_scope、
actual_adoption，但这些仍是作者声明，不能证明前置读取或效果。详细当前采用、
不采用理由与时序留在process/planning/knowledge的实际记录中。

读者干净投影只解析四个当前已提交具名proof角色：

| role | 现有解析格式 |
|---|---|
| knowledge-node-return | 真实selected_nodes聚合，或原生lookup的nodes数组及包/版本/请求code/三个SHA256包络；节点含code和原知识正文 |
| knowledge-cu-return | 原composition-reading/1.0返回，full_body=true，entries.understanding保留完整CU正文，body_sha256匹配其UTF-8字节 |
| knowledge-read-command | 真实argv数组、整数returncode及实际执行记录；不是模型阅读证明 |
| knowledge-manifest | 原art-learning-pack/1.0 manifest，不改原契约或假冒版本 |

保留原返回文件的真实格式；不要只改原contract或填写full_body=true来伪造兼容。
如果原始结构不匹配，原件与差异必须留下，不能宣称读者已得到完整正文。
组合多个实际节点返回时，另存有原始字节引用和真实组合时点的当前包，不能
把晚整理说成首次读取时已存在。脚本、命令与原始读取结果应按执行版本保存，
process.events每项action/record/artifacts指向仍匹配哈希的实际文件。

author-only的history/revision/effect/self-evaluation等不进入干净知识投影。
投影不递归打开任意embedded path，只使用当前stage提交的四个proof快照。
只写CU编号、full_body标志、hash或实际使用自评不能替代完整返回或逐页读图。
unknown schema、缺少proof、hash不符都保留为unobserved；既不等于没有用知识，
也不等于知识适用性、实际模型阅读、设计质量或成本已经独立验证。

确切现有实现为`packages/workflow3/reader_knowledge.py:project`及其_nodes、
_compositions、_command、_manifest；不得为取得通过修改这些函数或当前读者包。
本说明不把已绑定任务的旧知识文件补写成原来就正确的记录。

## 当前Art原生锁与渲染清单

确切现有检查在`packages/workflow3/interfaces.py:capture`，不是旧3.x包装。
design.slides与Copy page.id页序一致；copy_structure_lock.authority为
presentation-only；graph_sha256使用`packages.copy_graph.model.digest(graph)`
的规范JSON digest，与原graph文件字节SHA可能不同；interface.sha256绑定当前
identity回执。原graph不变。audit_observations保持现有audit-only结构；不能
用art_content或expression_additions越权改Copy。

renders.slides为所有实际PNG/JPEG按页序的path/bytes/sha256，pptx引用实际渲染
来源PPTX。生成页图前不能编造清单，缓存采用须精确身份和真实导出来源。
process.events记录当时真实工作；规范锁、文件格式和全部引用通过不能代替
完整专业设计、逐页实际看图、字体、容量及目标应用编辑行为观察。

原生lookup包络兼容只保留同一专业字段白名单；不递归打开路径，不投影composition_readings或历史自评，不证明实际阅读或采用。未知包络继续unobserved。
