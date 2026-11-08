# 页码字段与实际PDF的诊断

本工具只读当前PPTX、实际PDF和绑定两者精确字节的renders清单，不启动Office、不另做渲染、不编辑源文件，也不新增门禁。它是Output核对的辅助证据，不能代替全页读图、canonical页码要求或目标应用观察。

    python -B TOOL/scripts/inspect_slide_number_fields.py \
      --pptx CURRENT.pptx --pdf CURRENT.pdf --renders CURRENT-renders.json \
      --output NEW-diagnostic.json

清单中pptx/pdf的SHA256和bytes必须与当前输入相符。不会打开清单内的原路径，复制或重命名后的同字节文件可以使用；检查前后再核源文件及清单哈希。匹配只证明所提供的文件身份，不是独立宿主对实际导出及时间顺序的认证。

脚本用现有Poppler pdftotext取得字词及位置，在PPTX显式slidenum字段的顶层文字形状区域寻找单个十进制字词，记录源缓存、候选实际数字、位置与match/disagreement/unobserved。缓存可能陈旧；match不表示页码政策正确，disagreement也不单独证明该改哪一边。PDF文本没有源对象ID，几何候选仍需实际页图复核。

群组/旋转/翻转或继承几何、非十进制数字、多字词歧义、字词落在形状范围外、页数或比例不对应等保留unobserved。未展开master/layout继承字段；没有显式字段不能推断没有适用页码。不会从全页其他数字猜页码，也不会扩大容差追逐预期答案。

输出保留诊断JSON、原始bbox XML和实际命令、退出码及墙钟收据。输入或提取失败返回非零并保留已产生的证据；歧义和不一致不自动给生产流程判pass/fail。实际源文件、全页图、七项QA、独立读者和预算继续遵守原契约；未观察的模型用量、金额、活跃时间不补造。

在已测LibreOffice环境，源字段缓存与实际PDF可能不同，源属性或字段存在不能当成显示已经兑现。本助手尚未证明能减少专业缺陷或成本，也没有解决导出器差异本身。
