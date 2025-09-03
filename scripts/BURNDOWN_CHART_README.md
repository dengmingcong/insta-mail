# Bug燃尽图生成器

这个脚本可以根据项目的bug数据生成可视化的燃尽图，帮助项目管理者跟踪bug的发现和解决进度。

## 功能特性

1. **双折线图**: 同时显示bug发现燃尽图和bug解决燃尽图
2. **时区支持**: 支持UTC+8 (Asia/Shanghai) 时区的本地时间显示
3. **周末标注**: 自动识别并用灰色背景标注周六和周日
4. **智能时间轴**: 根据项目时间跨度自动选择显示日期或小时
5. **数据点突出**: 每个数据点用圆点和方点突出显示
6. **灵活配置**: 支持自定义图表宽度、输入输出文件等

## 安装依赖

```bash
# 安装matplotlib（如果尚未安装）
pip install matplotlib
```

## 使用方法

### 基本使用

```bash
# 使用默认设置生成燃尽图
python generate_burndown_chart.py
```

### 高级选项

```bash
# 指定输入和输出文件
python generate_burndown_chart.py -i my_bugs.json -o my_chart.png

# 自定义图表宽度（像素）
python generate_burndown_chart.py -w 800

# 不显示图表窗口，只保存文件（适合自动化脚本）
python generate_burndown_chart.py --no-show

# 查看所有选项
python generate_burndown_chart.py --help
```

### 命令行参数说明

- `--input, -i`: 输入的bug数据JSON文件路径（默认: bugs.json）
- `--output, -o`: 输出的图表文件路径（默认: bug_burndown_chart.png）
- `--width, -w`: 图表宽度，单位像素（默认: 660）
- `--no-show`: 不显示图表窗口，只保存文件

## 数据格式

输入的JSON文件应包含bug数据列表，每个bug对象需要包含以下字段：

```json
[
  {
    "id": "77100",
    "title": "bug标题",
    "openedDate": "2025-06-24 12:24:42",
    "resolvedDate": "2025-06-24 14:52:13",
    "status": "closed",
    ...
  }
]
```

### 关键字段说明

- `openedDate`: bug发现时间，格式为 "YYYY-MM-DD HH:MM:SS"
- `resolvedDate`: bug解决时间，格式同上，未解决的bug此字段为空或 "0000-00-00 00:00:00"

## 图表说明

### Bug发现燃尽图（橙色圆点线）
- 起点：项目最早bug发现时间，纵坐标为总bug数量
- 终点：项目最晚bug发现时间，纵坐标为0
- 含义：随着时间推移，剩余未发现的bug数量逐渐减少

### Bug解决燃尽图（绿色方点线）
- 起点：项目最早bug解决时间，纵坐标为总bug数量  
- 终点：项目最晚bug解决时间，纵坐标为永久未解决的bug数量
- 含义：随着时间推移，剩余未解决的bug数量逐渐减少

### 周末标注
- 灰色背景区域表示周六和周日
- 帮助识别工作日和休息日对bug处理的影响

### 时间轴
- 时间跨度 < 1天：显示小时（HH:MM格式）
- 时间跨度 >= 1天：显示日期（MM-DD格式）
- 根据图表宽度自动调整时间分段数量

## 输出信息

脚本会输出以下统计信息：

```
=== Bug统计信息 ===
总Bug数量: 44
已解决Bug: 44
未解决Bug: 0
解决率: 100.0%
```

## 示例

使用项目中的 `bugs.json` 文件生成燃尽图：

```bash
python generate_burndown_chart.py
```

生成的图表将显示：
- 项目时间范围：2025-05-15 至 2025-07-03
- 双折线展示bug发现和解决趋势
- 周末背景置灰标注
- 详细的统计信息

## 故障排除

1. **找不到文件错误**: 确保输入的JSON文件存在且路径正确
2. **JSON格式错误**: 检查JSON文件格式是否正确
3. **图表显示问题**: 如果在无界面环境运行，使用 `--no-show` 选项
4. **中文显示问题**: 脚本会自动尝试使用系统中文字体

## 技术说明

- 所有时间都被解释为UTC+8本地时间（naive datetime）
- 图表使用matplotlib生成，支持高质量PNG输出
- 周末判断基于Python的weekday()方法（周六=5，周日=6）
- 时间分段算法根据图表宽度自动优化显示效果
