# 原生编辑默认行为

Art依据内容选好表达和对象后，使用本指南设置其原生编辑行为；这些API不选择媒介、分区或框线。已经选用的形状才用自带文字，已经选用的节点连接才登记连接端点；能力验证样例不作为页面编排示范。

图表文字另有作用范围：较宽的chart默认、轴、图例、整组数据标签、单个点标签及自定义rich-text runs不能互相冒充。按当前需要读取的文字核对实际样式，不用默认字号推定全部小字。当前python-pptx 1.0.2的`DataLabel.text_frame`访问会取得或创建自定义文字，属于内容模式选择；点的`position`与固定字串是否随数据变化是两件事。选用固定文字时保留数据、文字、选择器及映射的同步责任；现有窄wrap接口不把自动值转换为固定文字。普通框换行设置不覆盖图内标签，当前渲染与未来GUI变值/重排分别留证，不增加统一nowrap、字号或标注配额。

对已选文字对象使用 `packages.layout.native_text`：`write_native_text` 写原始逻辑段落，`prepare_native_text` 保留已有强调runs并设置原生行为。默认 `word_wrap=True`、`line_spacing=1.0`（浮点倍数，不是Pt），段前后用真实段落属性。自然句不要先按当前宽度批量插入回车/软换行。明确语义段落和项目仍可分段；技术字段等局部例外可显式传 `word_wrap=False` 或 `fixed_line_spacing_pt`，并传适用的 `exception_reason`，不升级成全稿模式。

`role='body'` 默认左/顶、段后6pt；`label/header/button/node` 默认水平/垂直居中、段后0pt，默认边距左右.12in/上下.06in，可按用途明确覆盖。`prepare_native_text(cell, ...)` 将垂直锚定写到真实cell而不是只写TextFrame。`semantic_table.plan/write` 默认native-wrap：`cells[].lines` 是测量估计，不逐条写成原生段落或硬分行；表头居中，数字正文按列语义右对齐，长正文顶部对齐。实际导出后记录真实行和现有容量/字形结果，不把估计当已保存的硬分行，不放宽现有validator。

```python
from packages.layout import prepare_native_text, write_native_text
from packages.layout import refresh_rectangular_connector

# 对象与关系由当前设计选定；此处不创建页面布局。
prepare_native_text(selected_body, role='body', line_spacing=1.15,
                    space_after_pt=8)
write_native_text(selected_labeled_shape, selected_label, role='label')
# 调用者程序移动节点后，刷新原已选连接；不是GUI跟随证明。
refresh_rectangular_connector(selected_connector)
```

`add_text_shape` 是一个含文字的AutoShape，移动/复制该节点主要操作一个对象。不要惯例性另盖textbox，不普遍合并无关正文单元。Python适配器shape对象的 `text` 也写入该图形自身；其text options支持 `textRole`、`wordWrap`、`lineSpacingMultiple`、`paraSpaceBeforePt/AfterPt`。旧 `breakLine` 仍可作为wordWrap别名；既有manifest显式breakLine=False按legacy选项保留，不把它变成新内容默认。固定行距选项为具名例外 `lineSpacingPt` + `textFlowExceptionReason`。本次新接口覆盖python-pptx路线，不声称其他适配器已具有同等行为。

连接节点用真正native connector与id/site，端箭头用其自身属性；普通装饰线的坐标接口不冒作节点附着。`add_rectangular_connector`沿已有窄范围：同页直接spTree中的非旋转/翻转普通矩形。目标对象身份、所选site、保存的路径与应用实际采用的入点分别核对；不得用连接成功或较短路径替换Art已选关系。结合当前整页检查路径和标签仍对应正确对象，未知重定位原因照留。`refresh_rectangular_connector`读取已登记目标重新计算程序坐标，不安装自动观察器；PowerPoint/WPS/LO交互拖动必须有实际证据才能称通过。原箭头API不移动独立标签；整块方向箭头可用原生AutoShape。

参见 `examples/native_editability.py` 编辑前后样例。原生XML、实际渲染和交互验证分别记录；未验GUI保持deferred。以上是生成默认与局部例外，不增加审批、质量门限或页面/图形配额，不改有限返工流程。

### 按需分离点值内容与格式来源

图表数值内容与格式来源分别验明：原生自动值可以使用独立数字格式和点标签字体，不必写成固定数值字串。可选set_point_value_label_formats仅对显式选中的现有自动点标签写numFmt，并拒绝custom text；不修改数据/字体/位置兄弟节点，也不声称GUI更新。sourceLinked=false只明确采用该数字格式；数据修改仍要同步图表缓存与工作簿，并实际核对显示及语义色彩/符号。已有固定文字保留其同步责任，不由本接口自动转换。

### 所选连接集合的维护范围

实施已批准的节点几何变更时，可按显式所选范围调用refresh_rectangular_connectors批量核验并刷新同页已登记直线连接；无效输入先于任何所选线更新被拒。它保留既有id/site、线自身箭头和样式，不自动发现全部关联边、不跟随独立标签、不改选site或走最短路线。不可借维护接口移动锁定Art的节点或重排文字；真实整页对应与目标应用拖动仍按各自证据报告，未知不改写为通过。
