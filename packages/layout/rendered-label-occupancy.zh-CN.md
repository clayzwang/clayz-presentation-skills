# 共同图域中的标签占位观察

这是可选的作者辅助，不是新的验收器。它针对一个具体问题：原生图表生成的数值标签与另外放置的解读注释，会不会争用当前导出图上的同一处空间？变量、期间或关系动作没有被说明，是另一类问题；矩形测量不能补出这些身份。

从当前实际PDF和本次需观察的少量标签开始，保存一个请求。例如：

```json
{
  "contract": "io.clayz.presentation.label-occupancy-request/1.0",
  "pages": [{
    "slide_id": "S05",
    "page_number": 5,
    "labels": [
      {"label_id": "volume", "text": "537.9", "kind": "native-chart-data-label", "native_name": "volume-chart/series0/point1", "search_box": [0.05, 0.35, 0.48, 0.75]},
      {"label_id": "growth", "text": "+14.9%", "kind": "manual-annotation", "native_name": "growth-note", "search_box": [0.30, 0.30, 0.48, 0.50]}
    ]
  }]
}
```

`page_number`是PDF中从1开始的实际页序；`slide_id`和`native_name`用于追踪作者选择，不会自动识别原生对象。`search_box`默认是归一化的左、上、右、下边界；若已有规格保存`[x,y,w,h]`，先转换成`[x,y,x+w,y+h]`。也可显式用`box_units:"pt"`传入PDF点坐标。搜索区域用于辨认当前文本，不等同于内部容量或语义边界。

```bash
python scripts/observe_label_occupancy.py current.pdf request.json --output observation.r01.json
```

工具只查找指定的当前渲染行，按去空白后的完整文本匹配，并保留同一行中相邻PDF词的联合范围。一个匹配才进入成对测量；缺失或多义都明确保留，不能解释成标签不存在。每对范围保存间距和可能相交，不设置净空阈值。输出固定为`observation-only`，已有输出路径会被拒绝，修订须另存。

回到真实页图解释结果。font-metric范围相交不证明可见墨迹碰撞，不相交也不证明留白舒适、归属清楚或读者理解；工具没有观察其他标签、物体、连接线、目标应用和未来编辑。若身份、期间或动作含义缺失，按当前有据内容选择图文表达，不用几何修整代替语义判断。不要为使用这个辅助而登记所有页面或新增制作关卡。
