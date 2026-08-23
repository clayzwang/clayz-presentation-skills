# Clayz Presentation Skills

[English](README.md) | [简体中文](README.zh-CN.md)

[![CI](https://github.com/clayzwang/clayz-presentation-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/clayzwang/clayz-presentation-skills/actions/workflows/ci.yml) · 当前版本：**v0.4.0**

**[进入交互式体验中心 →](https://clayzwang.github.io/clayz-presentation-skills/)**

Clayz Presentation Skills 是一套开源的五阶段演示文稿生产体系：

1. **Logic**：建立问题链、论证关系、证据和跨页不变量。
2. **Copy**：锁定全部可见文字、数字、断句和原子文案。
3. **Art Direction**：在不修改内容的前提下形成视觉制作计划。
4. **Output**：按照批准计划制作可编辑的演示文稿。
5. **Supervisor**：独立审计跨层漂移和证据，不静默重做设计。

## 本轮能力升级

这不是继续堆版式口诀，而是给Art Direction增加一套更强的“招式”，同时要求每一招都服从当前内容：

- **内容感知构图**：图像主导页必须先判断主体保护区、文案可放置区、裁切、对比度、视觉方向和遮罩必要性，再决定文字位置；记住一个广告版式本身不能成为答案。
- **模板与Icon语法**：模板、图表、表格、Icon和外部样例只作为经过审阅的候选。页面必须从Logic和Copy重新推导构图，说明每项资产的语义角色，保持图标家族判断一致，并记录来源与许可证据。
- **参考架构综合**：Art Direction 内置经过校验的 76 份官方架构材料索引，覆盖十家发布者，并配套双语的 16 张关系模式卡。八步方法从问题界定、来源选择、关系提取和模式组合，推进到任务化推导、页面转译、诊断和研究账本收口；整个过程不导入厂商母版。
- **有合同的灵活判断**：Art Direction计划升级到v1.4，固定的是必须显式回答的证据和决策，不固定坐标、Icon数量、填充比例或审美分数；最终仍以真实A/B渲染和专业判断为准。
- **固定回归**：11个完全合成的案例覆盖四类材料、四种跨页行为、内容感知画布、受控资产选择和参考架构房子图。图像主导页缺少画布证据、已选资产缺少许可记录，以及只有名词分层却没有责任或反馈的房子图，都会被测试拒绝。
- **Index-native 构图方法**：v0.4.0 增加已登记的 Composition Pattern、Failure Pattern 与 Dataset-ready Reference、Sequence 元数据。Pattern 选择、关联失败知识、被拒候选、约束和预期视觉效果全部绑定 Receipt；无匹配保持显式 `unresolved`。
- **Metadata-only Dataset 边界**：公开导出只包含稳定 ID、分类、来源修订与哈希及原创方法元数据，排除源原文、图片、坐标、字体、模板、企业资产、模型权重、生成物自动准入和自动审美真值。
- **人工准入反馈与 Benchmark**：v0.4.0 只在独立人工决定绑定记录精确哈希后才重新索引观察。私有 Learning 不进入公开 Catalog；固定 Provider 快照、四个检索用例、失败关闭的旧索引迁移和显式发布授权记录，会把漂移、虚构和未授权发布变成验证失败。

公开仓库仍不打包任何第三方模板、母版、Icon库、海报、数据集、模型或媒体。增强的是检索、判断、重构和合规引用能力，不是克隆一个外部素材库。

## 项目沿革

五阶段工作流及其首批五项核心能力，由 **clayz** 品牌独立设计并实现；在这一基础已经可以运行之后，项目才进入开放学习阶段，陆续研究并选择性融汇多个开源项目和研究成果。

因此，[PPT Master](https://github.com/hugohe3/ppt-master) 是后续参考来源之一，并非本项目的起点、Fork 基础或底层框架。具体文件是否需要署名，按 `provenance/` 中记录的来源、影响范围和再分发事实逐项判断。

## 核心边界

- 五个 Skill 只保存各自职责、方法和必要合同。
- 母版、字体、色板、版式角色、参考资料源、渲染器、兼容目标、交付档位和签名统一进入 `config/default.json`。
- 核心 Skill、合成示例和知识脚手架不包含任何内部PPT、PDF、模板、字体、截图或其衍生素材；`experience/` 仅保存隔离的公开数据产出证据，且不得进入知识库或参考语料。
- 自动评分、视觉相似度和显著性只能作为诊断信号，不能代替业务与艺术判断。
- 输出默认保持可编辑、可追溯，并在最终写盘后重新渲染检查。

## 验证

`VERSION` 是唯一发布版本真值，CI会校验插件清单、中央配置、PPT元数据、CITATION、README、体验中心和Changelog是否一致。发布维护者应运行 `python scripts/prepare_release.py X.Y.Z --date YYYY-MM-DD`，不要逐文件手改版本；具体流程见[`docs/releasing.md`](docs/releasing.md)。

完整克隆仓库，以保证五个 Skill 仍能访问共享配置、合同、验证器和空知识脚手架：

```bash
git clone <你的仓库地址> clayz-presentation-skills
cd clayz-presentation-skills
python -m pip install -r requirements.txt
python scripts/validate_all.py
```

然后在大模型或 Agent 宿主中注册、暴露 `skills/` 下的五个目录。应从 Logic 开始，并把每一阶段批准后的产物交给下一阶段。请保留仓库相对路径；只复制某一个 Skill 文件夹会丢失共享配置与合同。

解析完全合成的布局树示例：

```bash
python packages/layout/solve_relative_layout.py \
  examples/synthetic-business-review/layout-tree.json \
  /tmp/resolved-layout.json
```

解析、编译并求解完全合成的已登记 Layout Contract 示例：

```bash
python packages/layout/compile_layout_contract.py \
  examples/synthetic-layout-contract/comparison-request.json \
  examples/synthetic-layout-contract/comparison-instance.json \
  /tmp/layout-compilation.json \
  --receipt-output /tmp/layout-receipt.json \
  --resolution-output /tmp/layout-resolution.json \
  --resolved-output /tmp/layout-coordinates.json
```

编译器不消费 Theme 或 Visual Variant。没有已登记合同匹配时，它会输出显式
`unresolved` resolution，并拒绝凭空生成或编译 fallback contract。详见
[`docs/layout-contracts.zh-CN.md`](docs/layout-contracts.zh-CN.md)。

解析并编译完全合成的已登记 Composition Pattern，再导出公开的
metadata-only Dataset：

```bash
python packages/patterns/compile_composition_pattern.py \
  examples/synthetic-pattern-library/comparison-request.json \
  --resolution-output /tmp/pattern-resolution.json \
  --receipt-dir /tmp/pattern-receipts \
  --plan-output /tmp/composition-plan.json

python packages/patterns/export_metadata_dataset.py \
  /tmp/clayz-metadata-dataset.json
```

Pattern compiler 不产生坐标，也不消费 Theme、Visual Variant、Layout Contract
或 Layout Tree。Pattern 或任何关联 Failure Pattern 未登记、未召回、多义、
权利不允许或哈希陈旧时都会拒绝编译。详见
[`docs/pattern-dataset-library.zh-CN.md`](docs/pattern-dataset-library.zh-CN.md)。

验证合成反馈闭环、Retrieval Benchmark、迁移报告与发布授权门禁：

```bash
python scripts/validate_feedback_benchmark.py
```

就绪记录要求五项证据门禁全部通过，并在 merge、不可变 Tag、发布或 Experience Center 当前版本更新前记录另一次明确人工决定。详见
[`docs/feedback-benchmark-release-readiness.zh-CN.md`](docs/feedback-benchmark-release-readiness.zh-CN.md)。

实验性 PptxGenJS 路线隔离在 `packages/adapters/pptxgenjs/`。其源码通过语法检查，但由于当前上游依赖链存在尚未修复的拒绝服务公告，中央配置默认阻断运行；任何评估前都应先阅读该目录 README。

## 运行环境与依赖

- 核心脚本需要Python 3.10或更高版本；位图准备、视觉节奏和文件体积检查使用Pillow，机器可读来源清单校验使用PyYAML。
- GitHub Actions会分别使用Python 3.10、3.11和3.12验证，并在发布前用`--help`启动所有公开命令行入口。
- 真正生成PPTX需要具备演示文稿能力的Agent环境，或另行提供原生演示工具、PptxGenJS、python-pptx等后端。
- 完整生产QA需要能够重开并渲染最终PPTX的环境，例如PowerPoint、WPS或LibreOffice。
- 当前仓库提供Skill、合同、集中配置、验证器、本地知识运行层、相对布局求解器、执行账本、签名工具和一个默认禁用的实验性可编辑对象适配器；它仍不是一条命令即可调用任意模型的独立Runner。
- MCP不是必需依赖。能读取Skill并调用本地工具的大模型宿主可直接运行；只有需要统一接入远程存储、检索、渲染或其他外部服务时，才需要另建MCP接口。

## 中英文路由

`config/default.json`默认使用`en-US`，同时支持`zh-CN`。每份深层reference都有英文主文件（如`references/example.md`）和中文平行文件（如`references/example.zh-CN.md`）。每个Skill先解析任务locale，再只读取一种语言；只有用户明确要求翻译对照时才同时加载。最终PPT使用何种语言由任务决定，不受说明文档语言强制影响。

## 知识库、持续学习与检索索引

公开仓库在`knowledge/`中提供一套刻意保持为空的可移植脚手架：

- Logic、Copy、Art Direction和Output四个学习区；
- 一个按文件类型保存的共享资料区；
- 空的资产索引与人工准入索引；
- 说明检索、写回和知识晋升边界的阶段导航。

Supervisor不建立独立学习库，而是把可复用观察返回给对应责任层。生成物、自动评分、使用次数和Supervisor意见都不得自动升级为正式参考。

下载仓库不会创建、读取或连接ChatGPT Library。默认资料提供者是本地文件系统；其他运行环境可以另行提供适配器，把同一结构映射到ChatGPT Library或其他存储系统，但本项目不捆绑、也不强制依赖此类适配器。详见[`knowledge/README.md`](knowledge/README.md)与[`knowledge/registry/schema.md`](knowledge/registry/schema.md)。

v0.2.0 已让脚手架实际可运行，v0.4.0 Stage 5 又把本地索引升级为 v2：`scripts/knowledge_cli.py` 可登记、单独人工准入、建索引、检索和记录观察；Learning 只有在独立人工准入绑定相同哈希后才进入索引。未准入或哈希变化的来源都会被排除。详见[`docs/knowledge-runtime.zh-CN.md`](docs/knowledge-runtime.zh-CN.md)。

## 公开成长边界

v0.2.0 增加的是可复用工程能力，不代替使用者吸收“人性”。核心 Skill、合成示例和知识脚手架仍不附带被准入的真实PPT案例、审美语料、个人偏好档案、企业风格、模板或母版；`experience/` 可以保存隔离的公开数据产出证据，但永不自动晋升为知识或参考。每位使用者可通过受治理的空知识架构自行成长。明确不学习的技术与逐项“采用／不采用”边界见[`docs/source-adoption.zh-CN.md`](docs/source-adoption.zh-CN.md)。

发布检查支持通过 `CLAYZ_RELEASE_DENYLIST` 或 `scripts/check_release_hygiene.py --denylist` 传入未跟踪的本地禁用词表。组织名称和源材料短语只应保存在该本地文件中，不得写入公开仓库。

在GitHub CI中，可把UTF-8禁用词表做Base64编码后保存为仓库Secret `CLAYZ_RELEASE_DENYLIST_B64`。工作流只在Runner中临时解码，不会把词表写入仓库。正式发布前还应按[`SECURITY.md`](SECURITY.md)启用GitHub私密漏洞报告。

## Clayz签名

生成文件可写入非可见的自定义文档属性，包括 `clayz`、项目版本和命名空间。签名不会增加隐藏页面、透明文字、设备标识、网络回传或不可删除水印。

写入签名：

```bash
python scripts/stamp_pptx_metadata.py deck.pptx --config config/default.json
```

只删除 Clayz 自有属性并保留其他文档元数据：

```bash
python scripts/stamp_pptx_metadata.py deck.pptx --config config/default.json --remove
```

## 引用与公开边界

感谢 PPT Master、PPTAgent、DeepPresenter、pom、VASCAR、PosterO、PosterLayout、Scan-and-Print、CreatiPoster、Tahta、MiniMax Skills、PosterCopilot、PosterVerse 与 PptxGenJS 的作者和贡献者。它们是本项目形成首批五项核心能力之后陆续研究的后续来源，只作为明确标识的概念启发、论文引用或可选公开 API 路线；准确修订、许可、引用限制与影响范围记录在 `provenance/manifest.yaml`。仓库不打包其源码快照、提示词、参考页、模板、媒体、数据集或模型；`examples/` 全部为合成数据。`experience/` 中的公开数据截图与PPT仅作为产出证据，并由 `experience/case-manifest.json` 和发布卫生检查单独治理。

参考架构综合方法还特别感谢 [IBM Think Architectures](https://www.ibm.com/think/architectures)、[Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/)、[Google Cloud Architecture Center](https://cloud.google.com/architecture)、[AWS Architecture Center](https://aws.amazon.com/architecture/)、[Oracle Architecture Center](https://docs.oracle.com/solutions/)、[SAP Architecture Center](https://architecture.learning.sap.com/)、[NVIDIA Enterprise Reference Architectures](https://docs.nvidia.com/enterprise-reference-architectures/)、[Databricks 参考架构](https://docs.databricks.com/aws/en/lakehouse-architecture/reference)、[Snowflake 架构指南](https://www.snowflake.com/en/developers/guides) 与 [Apple Platform Security](https://support.apple.com/guide/security/welcome/web) 背后的架构师、技术作者、设计师、工程师和审阅者。索引只记录链接和提炼后的关系，不再分发任何源架构图、原文、图标、品牌视觉、母版、模板、坐标或媒体。

本项目采用 Apache-2.0 许可证，来源和引用见 `NOTICE`、`CITATION.cff` 与 `provenance/`。

