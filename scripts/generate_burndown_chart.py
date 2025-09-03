#!/usr/bin/env python3
"""
生成项目bug燃尽图的脚本。

此脚本读取bugs.json文件，生成包含bug发现燃尽图和bug解决燃尽图的图表。
图表包含以下特性：
1. 双折线图：bug发现燃尽图和bug解决燃尽图
2. 周末背景置灰标注
3. 横坐标显示UTC+8时区的本地时间
4. 根据时间跨度智能显示日期或小时
5. 每个数据点用圆点突出显示
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def load_bugs_data(file_path: str = "bugs.json") -> List[Dict]:
    """加载bug数据from JSON文件。"""
    with open(file_path, "r", encoding="utf-8") as f:
        bugs = json.load(f)
    return bugs


def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期时间字符串，返回naive datetime（对应UTC+8本地时间）。

    Args:
        date_str: 格式为 "2025-06-24 12:24:42" 的日期字符串

    Returns:
        解析后的naive datetime对象，或None如果解析失败
    """
    if not date_str or date_str == "0000-00-00 00:00:00":
        return None

    try:
        # 假设所有时间都是UTC+8本地时间
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def get_time_range(bugs: List[Dict]) -> Tuple[datetime, datetime]:
    """获取所有bug的时间范围。

    Returns:
        (最早时间, 最晚时间)
    """
    opened_dates = []
    resolved_dates = []

    for bug in bugs:
        opened_date = parse_datetime(bug.get("openedDate"))
        if opened_date:
            opened_dates.append(opened_date)

        resolved_date = parse_datetime(bug.get("resolvedDate"))
        if resolved_date:
            resolved_dates.append(resolved_date)

    # 找到最早的开始时间
    min_opened = min(opened_dates) if opened_dates else datetime.now()
    min_resolved = min(resolved_dates) if resolved_dates else datetime.now()
    start_time = min(min_opened, min_resolved)

    # 找到最晚的结束时间
    max_opened = max(opened_dates) if opened_dates else datetime.now()
    max_resolved = max(resolved_dates) if resolved_dates else datetime.now()
    end_time = max(max_opened, max_resolved)

    return start_time, end_time


def calculate_segments(
    start_time: datetime, end_time: datetime, chart_width: int = 660
) -> List[datetime]:
    """根据时间跨度和图表宽度计算时间段分割点。

    Args:
        start_time: 开始时间
        end_time: 结束时间
        chart_width: 图表宽度（像素）

    Returns:
        时间分割点列表
    """
    time_span = end_time - start_time

    # 根据时间跨度决定分段数量，大约每80-100像素一个分段
    num_segments = max(6, min(20, chart_width // 80))

    # 如果时间跨度小于1天，使用小时分割
    if time_span.total_seconds() < 24 * 3600:
        # 按小时分割
        segment_duration = time_span.total_seconds() / num_segments
        segments = []
        for i in range(num_segments + 1):
            segments.append(start_time + timedelta(seconds=i * segment_duration))
    else:
        # 按天分割
        segment_duration = time_span.days / num_segments
        if segment_duration < 1:
            segment_duration = 1
        segments = []
        for i in range(num_segments + 1):
            segments.append(start_time + timedelta(days=i * segment_duration))

    return segments


def generate_discovery_burndown(
    bugs: List[Dict], segments: List[datetime]
) -> Tuple[List[datetime], List[int]]:
    """生成bug发现燃尽图数据。

    Args:
        bugs: bug数据列表
        segments: 时间分割点

    Returns:
        (时间点列表, 剩余未发现bug数量列表)
    """
    total_bugs = len(bugs)

    # 获取所有开启日期
    opened_dates = []
    for bug in bugs:
        opened_date = parse_datetime(bug.get("openedDate"))
        if opened_date:
            opened_dates.append(opened_date)

    opened_dates.sort()

    # 生成燃尽数据
    x_data = []
    y_data = []

    for segment_time in segments:
        # 计算到此时间点已发现的bug数量
        discovered_count = sum(1 for date in opened_dates if date <= segment_time)
        remaining_count = total_bugs - discovered_count

        x_data.append(segment_time)
        y_data.append(max(0, remaining_count))  # 确保不为负数

    return x_data, y_data


def generate_resolution_burndown(
    bugs: List[Dict], segments: List[datetime]
) -> Tuple[List[datetime], List[int]]:
    """生成bug解决燃尽图数据。

    Args:
        bugs: bug数据列表
        segments: 时间分割点

    Returns:
        (时间点列表, 剩余未解决bug数量列表)
    """
    total_bugs = len(bugs)

    # 获取所有解决日期
    resolved_dates = []
    unresolved_count = 0

    for bug in bugs:
        resolved_date = parse_datetime(bug.get("resolvedDate"))
        if resolved_date:
            resolved_dates.append(resolved_date)
        else:
            unresolved_count += 1

    resolved_dates.sort()

    # 生成燃尽数据
    x_data = []
    y_data = []

    for segment_time in segments:
        # 计算到此时间点已解决的bug数量
        resolved_count = sum(1 for date in resolved_dates if date <= segment_time)
        remaining_count = total_bugs - resolved_count

        x_data.append(segment_time)
        y_data.append(
            max(unresolved_count, remaining_count)
        )  # 最少为永久未解决的bug数量

    return x_data, y_data


def add_weekend_shading(ax, start_time: datetime, end_time: datetime):
    """为图表添加周末背景阴影。"""
    current = start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    while current <= end_time:
        # 0=周一, 6=周日
        if current.weekday() >= 5:  # 周六(5)和周日(6)
            weekend_start = mdates.date2num(current)
            weekend_end = mdates.date2num(current + timedelta(days=1))
            ax.axvspan(weekend_start, weekend_end, alpha=0.2, color="gray", zorder=0)

        current += timedelta(days=1)


def format_time_axis(ax, segments: List[datetime]):
    """格式化时间轴标签。"""
    time_span = segments[-1] - segments[0]

    # 将datetime转换为matplotlib的数值格式
    segment_nums = [mdates.date2num(seg) for seg in segments]

    # 设置x轴标签
    ax.set_xticks(segment_nums)

    if time_span.total_seconds() < 24 * 3600:
        # 小于1天，显示小时
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.tick_params(axis="x", rotation=45)
    else:
        # 大于1天，显示日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        ax.tick_params(axis="x", rotation=45)


def create_burndown_chart(
    bugs: List[Dict],
    output_file: str = "bug_burndown_chart.png",
    chart_width: int = 660,
    show_plot: bool = True,
):
    """创建bug燃尽图。

    Args:
        bugs: bug数据列表
        output_file: 输出文件名
    """
    # 设置中文字体支持
    plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # 获取时间范围
    start_time, end_time = get_time_range(bugs)

    # 计算时间分割点
    segments = calculate_segments(start_time, end_time, chart_width)

    # 生成燃尽数据
    discovery_x, discovery_y = generate_discovery_burndown(bugs, segments)
    resolution_x, resolution_y = generate_resolution_burndown(bugs, segments)

    # 创建图表，设置为指定宽度
    fig_width = chart_width / 100  # 转换为英寸
    fig_height = fig_width * 0.618  # 黄金比例
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # 添加周末背景阴影
    add_weekend_shading(ax, start_time, end_time)

    # 绘制发现燃尽图 - 使用matplotlib能接受的datetime对象
    ax.plot(
        mdates.date2num(discovery_x),
        discovery_y,
        "o-",
        linewidth=2,
        markersize=6,
        label="Bug发现燃尽图",
        color="#ff7f0e",
        alpha=0.8,
    )

    # 绘制解决燃尽图
    ax.plot(
        mdates.date2num(resolution_x),
        resolution_y,
        "s-",
        linewidth=2,
        markersize=6,
        label="Bug解决燃尽图",
        color="#2ca02c",
        alpha=0.8,
    )

    # 设置标题和标签
    ax.set_title(
        f"项目Bug燃尽图\n(数据时间范围: {start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')})",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("时间", fontsize=12)
    ax.set_ylabel("剩余Bug数量", fontsize=12)

    # 格式化时间轴
    format_time_axis(ax, segments)

    # 设置网格
    ax.grid(True, alpha=0.3)

    # 添加图例
    ax.legend(loc="upper right", fontsize=11)

    # 设置y轴从0开始
    ax.set_ylim(bottom=0)

    # 调整布局
    plt.tight_layout()

    # 保存图表为高质量PNG
    plt.savefig(
        output_file, dpi=150, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    print(f"燃尽图已保存至: {output_file}")

    # 根据参数决定是否显示图表
    if show_plot:
        plt.show()

    # 打印统计信息
    total_bugs = len(bugs)
    resolved_bugs = sum(
        1 for bug in bugs if parse_datetime(bug.get("resolvedDate")) is not None
    )
    unresolved_bugs = total_bugs - resolved_bugs

    print("\n=== Bug统计信息 ===")
    print(f"总Bug数量: {total_bugs}")
    print(f"已解决Bug: {resolved_bugs}")
    print(f"未解决Bug: {unresolved_bugs}")
    print(
        f"解决率: {resolved_bugs / total_bugs * 100:.1f}%"
        if total_bugs > 0
        else "解决率: 0%"
    )

    # 关闭图表以释放内存
    plt.close(fig)


def main():
    """主函数。"""
    import argparse

    parser = argparse.ArgumentParser(description="生成项目bug燃尽图")
    parser.add_argument(
        "--input",
        "-i",
        default="bugs.json",
        help="输入的bug数据JSON文件路径 (默认: bugs.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="bug_burndown_chart.png",
        help="输出的图表文件路径 (默认: bug_burndown_chart.png)",
    )
    parser.add_argument(
        "--width", "-w", type=int, default=660, help="图表宽度（像素）(默认: 660)"
    )
    parser.add_argument(
        "--no-show", action="store_true", help="不显示图表窗口，只保存文件"
    )

    args = parser.parse_args()

    try:
        # 加载bug数据
        print(f"正在加载bug数据从文件: {args.input}...")
        bugs = load_bugs_data(args.input)
        print(f"成功加载 {len(bugs)} 条bug记录")

        if len(bugs) == 0:
            print("警告: 没有找到bug数据")
            return

        # 生成燃尽图
        print("正在生成燃尽图...")
        create_burndown_chart(bugs, args.output, args.width, not args.no_show)

    except FileNotFoundError:
        print(f"错误: 找不到文件 {args.input}，请确保文件存在")
    except json.JSONDecodeError:
        print(f"错误: {args.input} 文件格式不正确")
    except Exception as e:
        print(f"错误: {str(e)}")
        raise


if __name__ == "__main__":
    main()
