const slides = [
  {
    src: "assets/cases/a-share/slide-02-summary.png",
    title: { en: "Executive synthesis", zh: "一句话结论" },
    alt: {
      en: "Executive synthesis slide from the A-share market analysis case",
      zh: "A股市场分析案例的一句话结论页",
    },
    caption: {
      en: "The deck opens with one conclusion, four evidence anchors, and an explicit risk budget.",
      zh: "用一句话结论、四个证据锚点和明确的风险预算建立整份报告的判断框架。",
    },
  },
  {
    src: "assets/cases/a-share/slide-03-regime-map.png",
    title: { en: "Four market regimes", zh: "四段行情切换" },
    alt: { en: "Four-stage market regime timeline", zh: "四阶段市场行情时间轴" },
    caption: {
      en: "The analysis separates June concentration, July deleveraging, August breadth recovery, and renewed rate pressure.",
      zh: "将6月科技集中、7月去杠杆、8月广度修复和利率再压制拆成四个不同阶段。",
    },
  },
  {
    src: "assets/cases/a-share/slide-04-index-risk.png",
    title: { en: "Index path risk", zh: "指数路径风险" },
    alt: { en: "Indexed performance comparison across four China market indices", zh: "四个中国市场指数的归一化走势对比" },
    caption: {
      en: "A calm endpoint can conceal an extreme path: STAR 50 nearly returned to its starting level after a deep drawdown.",
      zh: "终点接近平静并不代表路径平稳：科创50在深度回撤后几乎回到起点。",
    },
  },
  {
    src: "assets/cases/a-share/slide-05-liquidity.png",
    title: { en: "Liquidity confirmation", zh: "量能验证" },
    alt: { en: "Market turnover comparison across June, July, and August", zh: "6月至8月市场成交额对比" },
    caption: {
      en: "The rebound is treated as provisional until turnover and market breadth improve together.",
      zh: "只有成交额和上涨家数同步改善，反弹才能获得更可靠的确认。",
    },
  },
  {
    src: "assets/cases/a-share/slide-06-june-sector.png",
    title: { en: "June concentration", zh: "6月主题集中" },
    alt: { en: "June sector winners and representative companies", zh: "6月行业涨跌和代表公司" },
    caption: {
      en: "Sector and company evidence shows how technology and materials absorbed most incremental capital.",
      zh: "行业与公司证据共同说明科技和材料如何吸收了大部分增量资金。",
    },
  },
  {
    src: "assets/cases/a-share/slide-07-july-sector.png",
    title: { en: "July reversal", zh: "7月风格逆转" },
    alt: { en: "July sector reversal and overseas market comparison", zh: "7月行业逆转与海外市场对比" },
    caption: {
      en: "The selloff is framed as a reversal in crowded technology trades, not a uniform collapse in all China assets.",
      zh: "7月下跌被还原为拥挤科技交易的逆转，而非所有中国资产同步崩塌。",
    },
  },
  {
    src: "assets/cases/a-share/slide-13-growth.png",
    title: { en: "Growth company risk", zh: "成长公司风险" },
    alt: { en: "Growth company valuation and drawdown comparison", zh: "成长公司估值与回撤对比" },
    caption: {
      en: "Improving earnings do not automatically remove valuation, crowding, and long-duration-rate risk.",
      zh: "盈利改善并不会自动消除估值、拥挤度和海外长端利率风险。",
    },
  },
  {
    src: "assets/cases/a-share/slide-14-defense.png",
    title: { en: "Defensive assets are not interchangeable", zh: "防御资产并不同质" },
    alt: { en: "Defensive company comparison across coal, oil, banking, and gold", zh: "煤炭、石油、银行和黄金防御公司对比" },
    caption: {
      en: "Cash flow, commodity exposure, balance-sheet quality, and gold economics create different defensive behavior.",
      zh: "现金流、商品价格、资产质量和金价成本决定了完全不同的防御属性。",
    },
  },
  {
    src: "assets/cases/a-share/slide-15-september.png",
    title: { en: "September decision tests", zh: "9月观察清单" },
    alt: { en: "September macro events and four decision questions", zh: "9月宏观事件和四个确认问题" },
    caption: {
      en: "The deck ends with observable tests for liquidity, breadth, style leadership, and external rates.",
      zh: "以量能、广度、风格和外部利率四个可观察问题结束整份报告。",
    },
  },
];

const slideDecks = {
  case: slides,
  release: [
    {
      src: "assets/cases/v0.4.0-capability-deck/slide-01-index-foundation.png",
      title: { en: "Stage 1 · Index Foundation", zh: "阶段1 · Index Foundation" },
      alt: { en: "Index Foundation capability slide", zh: "Index Foundation 能力页" },
      caption: {
        en: "Provider-aware retrieval begins with auditable receipts and explicit unresolved fallbacks.",
        zh: "从带可审计回执和显式 unresolved fallback 的 Provider-aware 检索开始。",
      },
    },
    {
      src: "assets/cases/v0.4.0-capability-deck/slide-03-capability-index.png",
      title: { en: "Stage 2 · Capability Index", zh: "阶段2 · Capability Index" },
      alt: { en: "Capability Index routing slide", zh: "Capability Index 能力路由页" },
      caption: {
        en: "Capability routing makes supported paths and unresolved gaps visible before generation.",
        zh: "能力路由在生成前明确展示可用路径和未解决缺口。",
      },
    },
    {
      src: "assets/cases/v0.4.0-capability-deck/slide-05-layout-contract.png",
      title: { en: "Stage 3 · Layout Contract", zh: "阶段3 · Layout Contract" },
      alt: { en: "Layout Contract compilation slide", zh: "Layout Contract 编译页" },
      caption: {
        en: "Registered layout contracts compile intent into renderer-neutral slide objects.",
        zh: "已登记的布局契约将意图编译为与渲染器无关的幻灯片对象。",
      },
    },
    {
      src: "assets/cases/v0.4.0-capability-deck/slide-07-pattern-library.png",
      title: { en: "Stage 4 · Pattern & Dataset Library", zh: "阶段4 · Pattern 与 Dataset Library" },
      alt: { en: "Governed pattern and dataset library slide", zh: "受控 Pattern 与 Dataset Library 页面" },
      caption: {
        en: "Composition patterns, failure patterns, and dataset metadata stay governed and traceable.",
        zh: "Composition Pattern、Failure Pattern 与数据集元数据保持受控且可追溯。",
      },
    },
    {
      src: "assets/cases/v0.4.0-capability-deck/slide-09-feedback-learning.png",
      title: { en: "Stage 5 · Feedback, Benchmark & Readiness", zh: "阶段5 · Feedback、Benchmark 与 Readiness" },
      alt: { en: "Human-admitted feedback learning slide", zh: "人工准入反馈学习页" },
      caption: {
        en: "Human-admitted feedback and fixed benchmarks gate what the system is ready to learn.",
        zh: "人工准入反馈与固定基准共同约束系统可以学习的内容。",
      },
    },
  ],
  "chatbi-house": [
    {
      src: "assets/cases/chatbi-house/slide-01-architecture-house.png",
      title: { en: "Enterprise cognitive architecture", zh: "企业认知架构" },
      alt: {
        en: "ChatBI enterprise cognitive architecture house slide",
        zh: "ChatBI 企业认知架构房子图",
      },
      caption: {
        en: "A single editable slide connects business applications, governed data, reasoning services, controls, and learning feedback.",
        zh: "一张可编辑页面连接经营应用、受控数据、推理服务、运营治理和学习反馈。",
      },
    },
  ],
  chatbi: [
    {
      src: "assets/cases/chatbi-cognitive-system/slide-01-cover.png",
      title: { en: "Challenge framing", zh: "挑战定义" },
      alt: {
        en: "Cover of the ChatBI enterprise cognitive system advisory deck",
        zh: "ChatBI 企业认知系统建议材料封面",
      },
      caption: {
        en: "The advisory opens by reframing ChatBI from metric lookup to enterprise cognition.",
        zh: "从查指标重新定义问题：企业真正需要的是认知系统。",
      },
    },
    {
      src: "assets/cases/chatbi-cognitive-system/slide-03-architecture-house.png",
      title: { en: "Architecture and unresolved questions", zh: "架构与未决问题" },
      alt: {
        en: "Architecture house and six unanswered enterprise questions",
        zh: "企业认知架构房子图与六个未决问题",
      },
      caption: {
        en: "The architecture view exposes the operating questions that a platform diagram alone cannot answer.",
        zh: "架构图同时暴露单靠平台分层无法回答的运营问题。",
      },
    },
    {
      src: "assets/cases/chatbi-cognitive-system/slide-04-dupont-tree.png",
      title: { en: "Top-down DuPont metric tree", zh: "自上而下的杜邦指标树" },
      alt: { en: "Traditional multi-level DuPont metric tree", zh: "传统多层杜邦指标树" },
      caption: {
        en: "A top-down metric tree clarifies decomposition while revealing where interpretation still requires people.",
        zh: "自上而下的指标拆解既建立结构，也明确哪些解释仍需人工判断。",
      },
    },
    {
      src: "assets/cases/chatbi-cognitive-system/slide-06-semantic-layer-trap.png",
      title: { en: "The semantic-layer shortcut", zh: "语义层捷径" },
      alt: { en: "Semantic layer accountability trap", zh: "语义层责任归属陷阱" },
      caption: {
        en: "A semantic layer can standardize definitions, but it cannot absorb human accountability.",
        zh: "语义层可以统一定义，却不能替人承担判断责任。",
      },
    },
    {
      src: "assets/cases/chatbi-cognitive-system/slide-08-cognitive-loop.png",
      title: { en: "Enterprise cognitive loop", zh: "企业认知闭环" },
      alt: { en: "Enterprise cognitive operating loop", zh: "企业认知运营闭环" },
      caption: {
        en: "Trustworthy enterprise cognition depends on a closed operating loop, not another isolated platform layer.",
        zh: "可信企业认知依赖运营闭环，而不是再增加一个孤立的平台层。",
      },
    },
    {
      src: "assets/cases/chatbi-cognitive-system/slide-10-triad-methodology.png",
      title: { en: "Triad methodology", zh: "三元方法论" },
      alt: { en: "Triad methodology for enterprise cognition", zh: "企业认知三元方法论" },
      caption: {
        en: "The methodology aligns evidence, reasoning, and accountable action.",
        zh: "方法论将证据、推理和可问责行动对齐。",
      },
    },
    {
      src: "assets/cases/chatbi-cognitive-system/slide-11-closing-question.png",
      title: { en: "The closing governance question", zh: "最后的治理问题" },
      alt: { en: "Closing question about trustworthy evidence", zh: "关于可信证据的收尾问题" },
      caption: {
        en: "The deck closes by asking what evidence the organization is prepared to trust and act on.",
        zh: "材料最终追问：组织准备信任什么证据，并据此采取行动？",
      },
    },
  ],
  nodecharts: [
    {
      src: "assets/cases/nodejs-chart-engine-v0.5.0/slide-01-global-oil-sankey.png",
      title: { en: "Oil supply and demand do not share one center", zh: "全球石油生产与消费重心并不重合" },
      alt: {
        en: "Sankey slide comparing 2024 global oil production and consumption structures",
        zh: "比较2024年全球石油生产与消费结构的桑基图页面",
      },
      caption: {
        en: "ECharts Sankey widths compare each country's share on independently normalized production and consumption sides; they do not represent bilateral trade.",
        zh: "ECharts 桑基图分别归一化生产端与消费端的国家份额；流线不表示双边贸易。",
      },
    },
    {
      src: "assets/cases/nodejs-chart-engine-v0.5.0/slide-02-global-age-radial.png",
      title: { en: "Age structures are diverging across countries", zh: "全球人口年龄结构正在拉开代际差距" },
      alt: {
        en: "Three-layer radial stacked-bar slide comparing 2024 population age structures",
        zh: "比较2024年人口年龄结构的三层径向堆叠图页面",
      },
      caption: {
        en: "Equal-width country sectors show three within-country age shares that sum to 100%, from very young Niger to deeply aged Japan.",
        zh: "等宽国家扇区用三层径向占比合计到100%，从年轻的尼日尔延伸到深度老龄化的日本。",
      },
    },
  ],
  styles: [
    {
      src: "assets/showcase/mckinsey-demo.png",
      title: { en: "Consulting structure", zh: "咨询结构" },
      alt: { en: "McKinsey-style consulting slide example", zh: "麦肯锡风格咨询页面示例" },
      caption: {
        en: "McKinsey-inspired study · conclusion-led hierarchy and disciplined evidence structure.",
        zh: "麦肯锡风格研究 · 结论先行的层级与严谨证据结构。",
      },
    },
    {
      src: "assets/showcase/bcg-demo.png",
      title: { en: "Strategic framing", zh: "战略框架" },
      alt: { en: "BCG-style consulting slide example", zh: "BCG 风格咨询页面示例" },
      caption: {
        en: "BCG-inspired study · strong strategic framing with a distinct visual point of view.",
        zh: "BCG 风格研究 · 清晰的战略框架和鲜明视觉观点。",
      },
    },
    {
      src: "assets/showcase/clayz-overview.png",
      title: { en: "System overview", zh: "系统总览" },
      alt: { en: "Clayz Presentation Skills workflow overview", zh: "Clayz 演示文稿技能工作流总览" },
      caption: {
        en: "Clayz visual language · a system overview that keeps workflow, governance, and output connected.",
        zh: "Clayz 视觉语言 · 将工作流、治理和输出连接起来的系统总览。",
      },
    },
  ],
};

const translations = {
  en: {
    brandSub: "Experience Center",
    navCase: "Full case",
    navVersions: "Versions",
    navReleaseDeck: "v0.4.0 deck",
    navNodeCharts: "Node.js charts",
    navChatbi: "ChatBI cases",
    navStyles: "Visual range",
    navRepo: "GitHub repository",
    heroTitle: "See what governed presentation generation can actually deliver.",
    heroLede:
      "Follow one complete public-data case from market evidence to a presentation-ready decision story — then download the editable PowerPoint.",
    advantageLabel: "THE CLAYZ ADVANTAGE",
    advantageArchitecture: "Clear architecture",
    advantageArchitectureText: "Separated stages and explicit contracts keep the system understandable and auditable.",
    advantageLearning: "Strong self-learning",
    advantageLearningText: "Governed learning quickly absorbs proven methods from many schools of thought.",
    advantageAdaptability: "High adaptability",
    advantageAdaptabilityText: "Personal requirements and corporate templates compose into one executable plan.",
    heroExplore: "Explore the full case",
    heroDownload: "Download editable PPTX",
    metricSlides: "slide full deck",
    metricPreviews: "selected previews",
    metricEditable: "editable output",
    metricRegimes: "market regimes",
    caseTitle: "A-share market regime and sector rotation",
    caseIntro:
      "A data-heavy commercial analysis case covering index paths, liquidity, sector rotation, representative companies, IPO funding pressure, and September uncertainty.",
    caseStatus: "Public output evidence",
    briefInput: "Input",
    briefInputValue: "Structured market workbook + analytical brief",
    briefJob: "Communication job",
    briefJobValue: "Explain four regime shifts and define the evidence required for September",
    briefOutput: "Output",
    briefOutputValue: "16-slide Chinese commercial analysis deck",
    briefGenerated: "Generated",
    capSynthesis: "Evidence synthesis",
    capNarrative: "Decision narrative",
    capCharts: "Chart selection",
    capBrand: "Company assets",
    capConsistency: "Cross-slide consistency",
    capEditable: "Editable PowerPoint",
    viewerKicker: "Selected slide",
    slideCaptionDefault:
      "The deck opens with one conclusion, four evidence anchors, and an explicit risk budget.",
    previousSlide: "Previous",
    nextSlide: "Next",
    evidenceTitle: "The output is the end of a governed chain.",
    evidenceLogic: "Logic",
    evidenceLogicText: "Separate four market regimes, define claims, and bind each claim to quantitative evidence.",
    evidenceCopy: "Copy",
    evidenceCopyText: "Compress the analysis into conclusion-led titles, key numbers, and explicit decision tests.",
    evidenceArt: "Art direction",
    evidenceArtText: "Assign visual weight, chart form, comparison structure, and cross-slide rhythm.",
    evidenceOutput: "Output + QA",
    evidenceOutputText: "Build editable slides, render the deck, and inspect consistency before delivery.",
    versionTitle: "What each public version established",
    versionIntro:
      "Releases are described by verifiable repository capability. Same-input visual comparisons will only be labeled as such when both outputs are preserved.",
    v1Title: "Governed foundation",
    v1Item1: "Five-stage Logic → Copy → Art Direction → Output → Supervisor workflow",
    v1Item2: "Central configuration, contracts, validators, and bilingual references",
    v1Item3: "Synthetic approved-handoff regression and CI across Python 3.10–3.12",
    currentRelease: "Current release",
    v2Title: "Production structure",
    v2Item1: "Human-admitted, hash-bound local knowledge runtime",
    v2Item2: "Renderer-neutral relative-layout solver and render contracts",
    v2Item3: "Bounded execution ledger and isolated experimental editable-object adapter",
    v3Title: "Index-native governed generation",
    v3Item1: "Provider-aware Index with auditable receipts and explicit unresolved fallbacks",
    v3Item2: "Registered Layout Contracts, Composition and Failure Patterns, and metadata-only dataset export",
    v3Item3: "Hash-bound private learning, fixed retrieval benchmarks, and fail-closed legacy migration",
    v4Title: "Expressive chart evidence",
    v4Item1: "One reusable dynamic viewer across every Experience Center slide group",
    v4Item2: "Keyboard, thumbnail, bilingual, responsive, and single-slide-aware interaction",
    v4Item3: "Reproducible Apache ECharts SSR assets with public data, source notes, and editable PPTX evidence",
    releaseDeckTitle: "Inside v0.4.0: five stages of governed generation",
    releaseDeckIntro:
      "A 10-slide English deck consolidates the evidence from Index Foundation through capability routing, Layout Contracts, governed patterns, and human-admitted feedback.",
    releaseDeckKicker: "Release capability material · 10 slides",
    releaseDeckName: "v0.4.0 governed-generation capability deck",
    releaseDeckText:
      "The editable source shows the registered, fail-closed path from retrieval receipts to resolved slide objects, including explicit unresolved fallbacks and evidence-backed learning gates.",
    releaseDeckDownload: "Download 10-slide English PPTX",
    releasePreviewIndex: "Stage 1 · Index Foundation",
    releasePreviewCapability: "Stage 2 · Capability Index",
    releasePreviewLayout: "Stage 3 · Layout Contract",
    releasePreviewPatterns: "Stage 4 · Pattern & Dataset Library",
    releasePreviewFeedback: "Stage 5 · Feedback, Benchmark & Readiness",
    nodeChartsTitle: "Node.js adds chart forms that remain presentation-ready",
    nodeChartsIntro:
      "A two-slide public-data case tests an open-source Node.js chart route on two difficult analytical questions: asymmetric oil structures and cross-country age composition.",
    nodeChartsKicker: "v0.5.0 chart-engine material · 2 slides",
    nodeChartsName: "Global oil and demographic structure",
    nodeChartsText:
      "Apache ECharts renders server-side SVG and sharp produces PowerPoint-safe PNG assets. The package includes the editable deck, web previews, source data, method notes, and a reproducible Node.js script.",
    nodeChartsDownload: "Download 2-slide editable PPTX",
    nodeChartsSource: "Inspect Node.js source",
    chatbiTitle: "From metric lookup to an enterprise cognitive system",
    chatbiIntro:
      "Two related Chinese-language outputs turn the ChatBI discussion into an architecture view and a compact advisory narrative. Both editable source decks are available below.",
    chatbiHouseKicker: "Architecture study · 1 slide",
    chatbiHouseTitle: "ChatBI enterprise cognitive architecture house",
    chatbiHouseText:
      "A single high-density architecture page connects business applications, semantic and reasoning services, governed data and computation, operating controls, and the learning feedback loop.",
    chatbiHouseDownload: "Download architecture PPTX",
    chatbiHouseCaption: "Enterprise cognitive architecture · editable PowerPoint",
    chatbiAdvisoryKicker: "Advisory material · 11 slides",
    chatbiAdvisoryTitle: "From ChatBI to an enterprise cognitive system",
    chatbiAdvisoryText:
      "The deck makes the failure modes visible: metric lookup is not analysis, a semantic layer cannot absorb human accountability, and trustworthy enterprise cognition requires an operating loop rather than another platform layer.",
    chatbiAdvisoryDownload: "Download 11-slide advisory PPTX",
    chatbiPreviewCover: "Challenge framing",
    chatbiPreviewHouse: "Architecture and unresolved questions",
    chatbiPreviewDupont: "Top-down DuPont metric tree",
    chatbiPreviewSemantic: "The semantic-layer shortcut",
    chatbiPreviewLoop: "Enterprise cognitive loop",
    chatbiPreviewTriad: "Triad methodology",
    chatbiPreviewQuestion: "The closing governance question",
    styleTitle: "One governed system, different visual languages",
    styleIntro:
      "These compact studies demonstrate visual adaptation. The full market case above demonstrates long-form analytical compression.",
    styleMck: "Consulting structure · McKinsey-inspired study",
    styleBcg: "Strategic framing · BCG-inspired study",
    styleClayz: "System overview · Clayz visual language",
    closingTitle: "The experience is evidence, not a promise.",
    closingText:
      "Inspect the slides, compare the release capability map, and open the editable PowerPoint before deciding whether the workflow fits your presentation work.",
    closingDownload: "Download the case deck",
    closingRepo: "Inspect the repository",
    footerBoundary:
      "Public output evidence only. Showcase artifacts are not admitted into the Clayz knowledge or reference corpus.",
    footerDisclaimer:
      "Company names and marks belong to their respective owners and do not imply affiliation. Market content is for demonstration only and is not investment advice.",
  },
  zh: {
    brandSub: "体验中心",
    navCase: "完整案例",
    navVersions: "版本能力",
    navReleaseDeck: "v0.4.0 材料",
    navNodeCharts: "Node.js 图表",
    navChatbi: "ChatBI 案例",
    navStyles: "视觉范围",
    navRepo: "GitHub 仓库",
    heroTitle: "直接看看这套受控演示文稿系统，最终究竟能交付什么。",
    heroLede: "沿着一个完整的公开数据案例，从市场证据走到可汇报的决策故事，并下载可编辑的 PowerPoint。",
    advantageLabel: "CLAYZ 核心优势",
    advantageArchitecture: "架构清晰",
    advantageArchitectureText: "阶段职责和合同边界明确，整套系统易理解、可审计。",
    advantageLearning: "自学习能力强",
    advantageLearningText: "通过受控学习快速吸纳百家之长，并保留来源与准入边界。",
    advantageAdaptability: "自适应能力强",
    advantageAdaptabilityText: "将个性化要求与企业模板快速拼接为一套可执行方案。",
    heroExplore: "查看完整案例",
    heroDownload: "下载可编辑 PPTX",
    metricSlides: "页完整报告",
    metricPreviews: "张精选预览",
    metricEditable: "可编辑输出",
    metricRegimes: "段市场行情",
    caseTitle: "A股市场路径与板块轮动深度分析",
    caseIntro: "一个高数据密度的商业分析案例，覆盖指数路径、量能、板块轮动、代表公司、IPO资金占用和9月不确定性。",
    caseStatus: "公开产出证据",
    briefInput: "输入",
    briefInputValue: "结构化市场工作簿 + 分析任务",
    briefJob: "沟通任务",
    briefJobValue: "解释四段行情切换，并明确9月行情成立需要哪些证据",
    briefOutput: "输出",
    briefOutputValue: "16页中文商业分析报告",
    briefGenerated: "生成时间",
    capSynthesis: "证据综合",
    capNarrative: "决策叙事",
    capCharts: "图表选择",
    capBrand: "公司素材",
    capConsistency: "跨页一致性",
    capEditable: "可编辑 PowerPoint",
    viewerKicker: "精选页面",
    slideCaptionDefault: "用一句话结论、四个证据锚点和明确的风险预算建立整份报告的判断框架。",
    previousSlide: "上一页",
    nextSlide: "下一页",
    evidenceTitle: "成品，是一条受控生产链的最后结果。",
    evidenceLogic: "逻辑",
    evidenceLogicText: "拆分四段市场行情，建立命题，并将每个判断绑定到定量证据。",
    evidenceCopy: "文案",
    evidenceCopyText: "将分析压缩为结论式标题、关键数字和明确的验证问题。",
    evidenceArt: "艺术指导",
    evidenceArtText: "确定视觉权重、图表形式、比较结构和整份报告的跨页节奏。",
    evidenceOutput: "输出与质检",
    evidenceOutputText: "制作可编辑页面、渲染整份报告，并在交付前检查一致性。",
    versionTitle: "每个公开版本真正建立了什么能力",
    versionIntro: "版本说明只使用仓库中可验证的能力；只有保存了同输入的两版结果，才会标记为视觉版本对比。",
    v1Title: "受控生产基础",
    v1Item1: "逻辑 → 文案 → 艺术指导 → 输出 → 监督的五阶段工作流",
    v1Item2: "统一配置、跨阶段契约、验证器和中英双语参考",
    v1Item3: "合成交接回归和 Python 3.10–3.12 持续集成",
    currentRelease: "当前版本",
    v2Title: "生产化结构",
    v2Item1: "人工准入、哈希绑定的本地知识运行时",
    v2Item2: "与渲染器无关的相对布局求解器和渲染契约",
    v2Item3: "有边界的执行账本和隔离的实验性可编辑对象适配器",
    v3Title: "Index-native 受治理生成",
    v3Item1: "带可审计回执和显式 unresolved fallback 的 Provider-aware Index",
    v3Item2: "已登记 Layout Contract、Composition/Failure Pattern 与 metadata-only Dataset 导出",
    v3Item3: "哈希绑定的私有 Learning、固定检索 Benchmark 与失败关闭的旧索引迁移",
    v4Title: "更具表达力的图表证据",
    v4Item1: "体验中心所有幻灯片组统一使用可复用动态 viewer",
    v4Item2: "支持键盘、缩略图、中英双语、移动端与单页自动适配",
    v4Item3: "公开数据、来源说明、可编辑 PPTX 与 Apache ECharts SSR 代码形成可复现证据",
    releaseDeckTitle: "深入 v0.4.0：受治理生成的五个阶段",
    releaseDeckIntro: "这份10页英文材料汇总了从 Index Foundation、能力路由和 Layout Contract，到受控 Pattern 与人工准入 Feedback 的阶段证据。",
    releaseDeckKicker: "版本能力材料 · 10页",
    releaseDeckName: "v0.4.0 受治理生成能力材料",
    releaseDeckText: "可编辑源文件展示了从检索回执到已解析幻灯片对象的登记式、失败关闭路径，并包含显式 unresolved fallback 与有证据支撑的学习门禁。",
    releaseDeckDownload: "下载10页英文 PPTX",
    releasePreviewIndex: "阶段1 · Index Foundation",
    releasePreviewCapability: "阶段2 · Capability Index",
    releasePreviewLayout: "阶段3 · Layout Contract",
    releasePreviewPatterns: "阶段4 · Pattern 与 Dataset Library",
    releasePreviewFeedback: "阶段5 · Feedback、Benchmark 与 Readiness",
    nodeChartsTitle: "用 Node.js 扩展表达力，同时保持演示文稿可交付",
    nodeChartsIntro: "这份两页公开数据案例，用开源 Node.js 图表链路检验两个高难度问题：非对称石油结构与跨国人口年龄构成。",
    nodeChartsKicker: "v0.5.0 图表引擎材料 · 2页",
    nodeChartsName: "全球石油与人口结构分析",
    nodeChartsText: "Apache ECharts 以 SSR 方式生成 SVG，sharp 输出适合 PowerPoint 的 PNG；材料同时提供可编辑 PPTX、网页预览、源数据、方法说明和可复用 Node.js 脚本。",
    nodeChartsDownload: "下载两页可编辑 PPTX",
    nodeChartsSource: "查看 Node.js 源码",
    chatbiTitle: "从查指标，走向企业认知系统",
    chatbiIntro: "两份相互关联的中文材料，将 ChatBI 讨论分别形成一页企业认知架构和一份紧凑的建议性叙事；下方均可下载可编辑源文件。",
    chatbiHouseKicker: "架构研究 · 1页",
    chatbiHouseTitle: "ChatBI 企业认知架构房子图",
    chatbiHouseText: "用一张高信息密度架构图，连接经营应用、语义与推理服务、受控数据与计算、运营治理，以及持续学习反馈闭环。",
    chatbiHouseDownload: "下载架构 PPTX",
    chatbiHouseCaption: "企业认知架构 · 可编辑 PowerPoint",
    chatbiAdvisoryKicker: "建议材料 · 11页",
    chatbiAdvisoryTitle: "从 ChatBI 到企业认知系统",
    chatbiAdvisoryText: "材料直观揭示几类失败道路：查指标不等于分析，语义层不能替人承担责任，可信企业认知需要完整运营闭环，而不是再叠一层平台。",
    chatbiAdvisoryDownload: "下载11页建议材料 PPTX",
    chatbiPreviewCover: "挑战命题",
    chatbiPreviewHouse: "架构与未决问题",
    chatbiPreviewDupont: "从上至下的杜邦指标树",
    chatbiPreviewSemantic: "语义层捷径的陷阱",
    chatbiPreviewLoop: "企业认知闭环",
    chatbiPreviewTriad: "三角方法论",
    chatbiPreviewQuestion: "最终的治理问题",
    styleTitle: "同一套受控系统，可以使用不同视觉语言",
    styleIntro: "三张短案例证明视觉适配能力；上方完整报告证明长篇商业分析的压缩能力。",
    styleMck: "咨询结构 · 麦肯锡风格研究",
    styleBcg: "战略表达 · BCG风格研究",
    styleClayz: "系统总览 · Clayz视觉语言",
    closingTitle: "体验中心提供的是证据，不是口号。",
    closingText: "先检查页面、比较版本能力，再打开可编辑 PowerPoint，判断这套工作流是否适合你的汇报工作。",
    closingDownload: "下载案例报告",
    closingRepo: "查看项目仓库",
    footerBoundary: "仅作为公开产出证据；展示文件不会进入 Clayz 知识库或参考语料。",
    footerDisclaimer: "公司名称及商标归各自权利人所有，不代表关联或背书；市场内容仅用于能力演示，不构成投资建议。",
  },
};

let activeLanguage = localStorage.getItem("clayz-experience-language") || "en";
const languageToggle = document.querySelector(".language-toggle");
const slideViewers = [];

function createSlideViewer(container, deck) {
  let activeIndex = 0;

  container.tabIndex = 0;
  container.classList.toggle("is-single-slide", deck.length === 1);
  container.innerHTML = `
    <div class="viewer-toolbar">
      <div>
        <span class="viewer-kicker"></span>
        <strong class="viewer-slide-title"></strong>
      </div>
      <div class="viewer-count" aria-live="polite">
        <span class="viewer-current">01</span>
        <span>/</span>
        <span class="viewer-total"></span>
      </div>
    </div>
    <figure class="slide-stage">
      <img class="viewer-active-slide" alt="" loading="lazy" decoding="async" />
      <figcaption class="viewer-slide-caption"></figcaption>
    </figure>
    <div class="viewer-controls">
      <button class="viewer-button viewer-previous" type="button"></button>
      <div class="thumbnail-strip" role="list"></div>
      <button class="viewer-button viewer-next" type="button"></button>
    </div>
  `;

  const activeSlide = container.querySelector(".viewer-active-slide");
  const slideTitle = container.querySelector(".viewer-slide-title");
  const slideCaption = container.querySelector(".viewer-slide-caption");
  const slideCurrent = container.querySelector(".viewer-current");
  const slideTotal = container.querySelector(".viewer-total");
  const viewerKicker = container.querySelector(".viewer-kicker");
  const previousButton = container.querySelector(".viewer-previous");
  const nextButton = container.querySelector(".viewer-next");
  const thumbnailStrip = container.querySelector(".thumbnail-strip");

  function renderThumbnails() {
    thumbnailStrip.innerHTML = "";

    deck.forEach((slide, index) => {
      const button = document.createElement("button");
      button.className = "thumbnail-button";
      button.type = "button";
      button.setAttribute("role", "listitem");
      button.setAttribute("aria-label", `${index + 1}. ${slide.title[activeLanguage]}`);
      button.setAttribute("aria-current", index === activeIndex ? "true" : "false");

      const image = document.createElement("img");
      image.src = slide.src;
      image.alt = "";
      image.loading = "lazy";
      button.appendChild(image);

      button.addEventListener("click", () => selectSlide(index));
      thumbnailStrip.appendChild(button);
    });
  }

  function selectSlide(index, scrollThumbnail = true) {
    activeIndex = (index + deck.length) % deck.length;
    const slide = deck[activeIndex];

    activeSlide.src = slide.src;
    activeSlide.alt = slide.alt[activeLanguage];
    slideTitle.textContent = slide.title[activeLanguage];
    slideCaption.textContent = slide.caption[activeLanguage];
    slideCurrent.textContent = String(activeIndex + 1).padStart(2, "0");

    const thumbnails = thumbnailStrip.querySelectorAll(".thumbnail-button");
    thumbnails.forEach((thumbnail, index) => {
      thumbnail.setAttribute("aria-current", index === activeIndex ? "true" : "false");
    });

    if (scrollThumbnail) {
      thumbnails[activeIndex]?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
    }
  }

  function renderLanguage() {
    viewerKicker.textContent = translations[activeLanguage].viewerKicker;
    previousButton.textContent = translations[activeLanguage].previousSlide;
    nextButton.textContent = translations[activeLanguage].nextSlide;
    thumbnailStrip.setAttribute("aria-label", activeLanguage === "zh" ? "幻灯片缩略图" : "Slide thumbnails");
    renderThumbnails();
    selectSlide(activeIndex, false);
  }

  previousButton.addEventListener("click", () => selectSlide(activeIndex - 1));
  nextButton.addEventListener("click", () => selectSlide(activeIndex + 1));
  container.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      selectSlide(activeIndex - 1);
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      selectSlide(activeIndex + 1);
    }
  });

  slideTotal.textContent = String(deck.length).padStart(2, "0");
  return { renderLanguage };
}

function setLanguage(language) {
  activeLanguage = language;
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  document.title =
    language === "zh" ? "Clayz 演示文稿技能 · 体验中心" : "Clayz Presentation Skills · Experience Center";

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (translations[language][key]) {
      element.textContent = translations[language][key];
    }
  });

  languageToggle.textContent = language === "en" ? "中文" : "EN";
  languageToggle.setAttribute("aria-label", language === "en" ? "切换到中文" : "Switch to English");
  localStorage.setItem("clayz-experience-language", language);

  slideViewers.forEach((viewer) => viewer.renderLanguage());
}

document.querySelectorAll("[data-slide-viewer]").forEach((container) => {
  const deck = slideDecks[container.dataset.slideViewer];
  if (deck?.length) {
    slideViewers.push(createSlideViewer(container, deck));
  }
});

languageToggle.addEventListener("click", () => setLanguage(activeLanguage === "en" ? "zh" : "en"));

setLanguage(activeLanguage);
