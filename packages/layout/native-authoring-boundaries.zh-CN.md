# 原生起页、显式位置与图例颜色角色

`packages.layout.native_page.add_native_page` 公开现有适配器的中性起页行为。调用者必须提供实际选定的 layout，可以指定背景；函数不读取 title/cover/body 角色，不创建短横、标题或正文预留区。使用空白 layout 时，返回页没有新增内容对象；使用用户母版 layout 时，保留它本身的占位符及继承，不私自剥离。

```python
slide = add_native_page(prs, layout=chosen_layout, background=background_rgb)
# 标题是普通的显式原生对象；其位置/空间由当前 Art 方案给出。
# 已有 render-manifest 路线仍逐个消费对象的 x/y/w/h 和字体样式。
```

中性初始化不是“永远留空页首”，也不决定标题该放哪。移除无用途的装饰后，要按当前内容重新分配标题、主证据与必要边距；不保留旧辅助函数的固定上区，也不靠轮换装饰制造差异。实际效果仍要在本轮图稿观察，函数没有空间利用或美学通过结论。

`packages.layout.native_chart_text.set_manual_legend_colors` 对现成 swatch 和文字框分别接受必填的 `mark_color`、`text_color`。它不生成图例位置，也不从 mark 的浅淡程度推断文字颜色：

```python
set_manual_legend_colors(swatch, label.text_frame,
                         mark_color='D8E0E2', text_color='667782')
```

浅色历史标记与可辨的身份文字可以同时成立，二者仍须通过邻近、色块和具名对象建立对应。是否使用相同颜色由 Art 决定；此接口没有统一黑字、自动调色、对比度门槛或 WCAG/PPT 合规声明。实际背景、字形、观看条件、图例归属和原生编辑行为分别检查。

## 作者局部选择的文字组合

既有 `text_flow.wrap` 的 `protected_terms` 可按当前对象选择字面短语、范围或范围与单位的组合；`authoring_text.measure_lines` 已转交该参数。任务 helper 也应逐次转交，不只在内部使用默认词项。显式选择会作用于本次输入的每个字面出现处；不自动推断全稿词典。

```python
lines = wrap(approved_text, actual_font, supplied_usable_width,
             protected_terms=(selected_phrase, selected_range_and_unit))
# measure_lines(..., protected_terms=...) 仍可使用；字体和区域由Art给出。
```

组合约束不会削弱原有日期、数值或Latin原子。若作者选择只是一个日期的子串，仍保留整个日期；若不同选择相互重叠，保护范围会并成一组，相邻但不重叠的组仍可在组间换行。超过给定宽度会明确报错，由作者重看空间或手工行，函数不缩字、不改原字符、不插入隐藏joiner。空集合表示不加词项保护，默认词项保持既有来源；本次没有扩题材词典。

合法断点、所选断点、对象容量和真实阅读效果分别判断。普通中文仍能逐字流动；只有当前重要读取单位受影响时才局部选择组合。手工语义分行仍是有效的Art动作，Output保留锁定行，不为应用后来的组合偏好重新排版。该窄实现不声明UAX14完整符合，也不替代原字体、字形、容量和目标应用检查。


## 显式选择已有图内点标签的换行

```python
from packages.layout.native_chart_text import set_point_label_wrapping
observation = set_point_label_wrapping(chart, [
    dict(series_index=0, point_index=0,
         expected_text=chosen_existing_literal, word_wrap=False),
])
```

函数先核对全部索引、重复选择、已有richText和完整文字，再只改所选bodyPr.wrap；索引是当前chart.series顺序中的零基索引。自动生成的数值标签/不存在的点文本会被拒绝，避免隐式转成固定标签。保留所有文字run、字号、position、样式兄弟节点、缓存和工作簿；调用本身不创建图例、类目或方向线。True写square，False写none，None清除该属性并恢复继承。已有硬换行不因False消失。返回可序列化的作者观察，不返回合格分数。

这是库既有TextFrame属性的受限集成，不是新排版引擎。宽度由当前图表软件分配；无换行也可能溢出或撞邻居。按实际任务比较默认布局、局部选择、图域变化和外置直标，后者须另核数值身份及更新联动。普通protected_terms不会自动作用于此图内richText，反之此调用也不调整普通文本。实际PPTX重开、原图页阅和原QA各保留范围，不对全图自动nowrap或统一字号。


## 显式选择现有直连接器的原生线端

```python
from packages.layout import set_connector_line_ends
set_connector_line_ends(line,
    head={"type": "oval", "w": "sm"},
    tail={"type": "triangle", "w": "med", "len": "med"})
# 后一次调用省略head，保留其全部属性；显式none与inherit不同。
set_connector_line_ends(line, tail={"type": "none"})
set_connector_line_ends(line, tail="inherit")
```

type可选none/triangle/stealth/diamond/oval/arrow；w/len可选sm/med/lg，未给属性保持原显式值或继承状态。所选mapping必须明确type；None保持整端不动。inherit删除所选headEnd/tailEnd节点，不删除a:ln或其他线属性，不保证主题中没有端标。所有所选输入和既有节点唯一性先核完，错误的第二端不能留下第一端的修改或新a:ln。新增节点按fill/dash/join、headEnd、tailEnd、extLst顺序插入，其余原生XML不规范化重写。

这只为同一slide直接spTree里的非零、非旋转直connector设置line格式，保留原flipH/flipV，不处理group或曲线。返回原Connector对象，不是JSON质量回执。它不自动挑业务方向、不路由、不绑目标、不创建/迁移独立head或label。标记尺寸相对线宽、继承与实际端向均需看当前原生导出；不是固定点数图标、无碰撞保证或GUI测试。已有attach_rectangular_connector负责显式矩形id/site和坐标吸附，独立文字仍不跟随；两种接口的责任不合并。
