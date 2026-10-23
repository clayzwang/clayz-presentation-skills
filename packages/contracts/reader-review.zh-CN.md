# 读者审读 — v0.20.5

当前流程见 [单轮返工与原读者复看](reader-cycle.zh-CN.md)。首次阅读仍须真实独立执行，先冻结理解，再对照 Logic/Copy。完整记录字段与命令见 [英文审读合同](reader-review.md)。

## 现有运行合同的成品对照字段

实际准备的成品packet绑定Art plan时，`comparison`还须包含`art_changes`：按该plan的`art_content.changes`原顺序逐项提供`change_id`、`assessment`（`justified`、`unsupported`或`uncertain`）、非空的有据`explanation`和`evidence`字符串。`pass`要求全部为`justified`。把当前plan绑定进第二遍evidence，并实际阅读每项变化；不能由首读finding数量推定变化覆盖。未绑定Art plan时，沿英文合同的四字段comparison。静态schema容许该字段；外部plan条件、ID和顺序仍由原运行验证器校验。

disposition及成品返工owner沿现有阶段枚举写`art-direction`，不是`art`。这里补明既有传输合同，不新增审读、返工额度，也不要求改写读者专业判断。
