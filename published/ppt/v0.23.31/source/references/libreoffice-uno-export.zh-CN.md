# LibreOffice UNO 导出方法

适用于预检已选择 LibreOffice、当前环境实际具备匹配的 Python UNO 桥的路线。本方法不启动 Office、不安装依赖、不改变后端、失败规则或预算。不可用时如实记录，不能声称已验证。

先由运行控制器在本任务专用 profile 启动一次允许的常驻 Office，保存完整命令、日志及启动时所有可观察进程身份。使用唯一 pipe。先调用 client 的 `ready` 操作建立真实 UNO 连接，不导出；再确认同 profile 唯一服务 PID/start_ticks 稳定至少一秒并保存采样。不能在服务就绪前把 bootstrap PID 当最终服务身份。

`scripts/libreoffice_uno_client.py --help` 给出参数。ready 需要 pipe、expected-profile、全新 receipt 路径。export 还需 ready 后锁定的 expected-pid/start-ticks、实际 PPTX source、全新 PDF output。客户端只连接已启动的服务，通过 loadComponentFromURL、storeToURL(impress_pdf_Export)、close 导出并关闭文档，逐次核验源字节及原服务身份，不自动重试。每次真实导出计入原渲染预算。

同一运行的后续导出继续连接同一个服务，不重新调用批量 --convert-to 来关闭常驻引擎。结束后才使用 shutdown；它实际调用 desktop.terminate。每次成功或失败均保留原始 receipt，不复用已存在 PDF/receipt 文件名。控制器仍需另行执行 PDF 页数、字体、全页转图及实际逐页读图。

Python 必须能实际导入与当前 LibreOffice/Python ABI 匹配的 uno/pyuno；系统现成依赖优先。局部依赖只能使用明确的命令作用域环境并保存真实来源/版本/哈希，不能把未安装或不匹配的桥写成可用。桥接客户端不是原生编辑行为或字体兼容性验收。

方法在一个 Linux LibreOffice 7.4.7 环境的两份一页合成文件上观察过同一 ready 服务连续两次导出和正常关闭。该范围不证明其他软件、复杂稿件、原生编辑或语义质量；启动瞬间的短命子进程可能低于采样分辨率。工具不含测试答案、公司稿、系统二进制或依赖安装器。

serve / ready / export / shutdown 必须使用同一实际执行权限与网络作用域，并复用同一profile / pipe及ready绑定的服务身份。受限作用域中的NoConnect先按真实失败留档，核对控制器原作用域；它本身不证明服务已退出，也不授权重启或新引擎。返回原已授权作用域继续连接或正常shutdown仍须核验原PID / start_ticks，并计入原预算；本说明不增加启动、导出或失败重试额度。
