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

const translations = {
  en: {
    brandSub: "Experience Center",
    navCase: "Full case",
    navVersions: "Versions",
    navReleaseDeck: "v0.4.0 deck",
    navChatbi: "ChatBI cases",
    navStyles: "Visual range",
    navRepo: "GitHub repository",
    heroTitle: "See what governed presentation generation can actually deliver.",
    heroLede:
      "Follow one complete public-data case from market evidence to a presentation-ready decision story — then download the editable PowerPoint.",
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
    stylePingan: "Business reporting · Ping An study",
    styleClayz: "System overview · Clayz visual language",
    styleDownloadTitle: "Four-slide visual adaptation pack",
    styleDownloadText: "Open the editable source behind the compact visual studies shown above.",
    styleDownloadButton: "Download 4-slide PPTX",
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
    navChatbi: "ChatBI 案例",
    navStyles: "视觉范围",
    navRepo: "GitHub 仓库",
    heroTitle: "直接看看这套受控演示文稿系统，最终究竟能交付什么。",
    heroLede: "沿着一个完整的公开数据案例，从市场证据走到可汇报的决策故事，并下载可编辑的 PowerPoint。",
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
    styleIntro: "四张短案例证明视觉适配能力；上方完整报告证明长篇商业分析的压缩能力。",
    styleMck: "咨询结构 · 麦肯锡风格研究",
    styleBcg: "战略表达 · BCG风格研究",
    stylePingan: "经营汇报 · 平安案例研究",
    styleClayz: "系统总览 · Clayz视觉语言",
    styleDownloadTitle: "四页视觉适配体验包",
    styleDownloadText: "打开上方四张视觉研究对应的可编辑源文件。",
    styleDownloadButton: "下载四页 PPTX",
    closingTitle: "体验中心提供的是证据，不是口号。",
    closingText: "先检查页面、比较版本能力，再打开可编辑 PowerPoint，判断这套工作流是否适合你的汇报工作。",
    closingDownload: "下载案例报告",
    closingRepo: "查看项目仓库",
    footerBoundary: "仅作为公开产出证据；展示文件不会进入 Clayz 知识库或参考语料。",
    footerDisclaimer: "公司名称及商标归各自权利人所有，不代表关联或背书；市场内容仅用于能力演示，不构成投资建议。",
  },
};

let activeIndex = 0;
let activeLanguage = localStorage.getItem("clayz-experience-language") || "en";

const activeSlide = document.querySelector("#active-slide");
const slideTitle = document.querySelector("#slide-title");
const slideCaption = document.querySelector("#slide-caption");
const slideCurrent = document.querySelector("#slide-current");
const thumbnailStrip = document.querySelector("#thumbnail-strip");
const languageToggle = document.querySelector(".language-toggle");

function renderThumbnails() {
  thumbnailStrip.innerHTML = "";

  slides.forEach((slide, index) => {
    const button = document.createElement("button");
    button.className = "thumbnail-button";
    button.type = "button";
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

function selectSlide(index) {
  activeIndex = (index + slides.length) % slides.length;
  const slide = slides[activeIndex];

  activeSlide.src = slide.src;
  activeSlide.alt = slide.alt[activeLanguage];
  slideTitle.textContent = slide.title[activeLanguage];
  slideCaption.textContent = slide.caption[activeLanguage];
  slideCurrent.textContent = String(activeIndex + 1).padStart(2, "0");

  const thumbnails = thumbnailStrip.querySelectorAll(".thumbnail-button");
  thumbnails.forEach((thumbnail, index) => {
    thumbnail.setAttribute("aria-current", index === activeIndex ? "true" : "false");
  });

  thumbnails[activeIndex]?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
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

  renderThumbnails();
  selectSlide(activeIndex);
}

document.querySelector("#previous-slide").addEventListener("click", () => selectSlide(activeIndex - 1));
document.querySelector("#next-slide").addEventListener("click", () => selectSlide(activeIndex + 1));
languageToggle.addEventListener("click", () => setLanguage(activeLanguage === "en" ? "zh" : "en"));

document.addEventListener("keydown", (event) => {
  const caseSection = document.querySelector("#case");
  const rect = caseSection.getBoundingClientRect();
  const caseIsVisible = rect.top < window.innerHeight && rect.bottom > 0;

  if (!caseIsVisible) return;
  if (event.key === "ArrowLeft") selectSlide(activeIndex - 1);
  if (event.key === "ArrowRight") selectSlide(activeIndex + 1);
});

setLanguage(activeLanguage);
