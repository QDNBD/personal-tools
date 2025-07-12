import matplotlib

matplotlib.use('TkAgg')  # 或者使用 'Qt5Agg'
import pandas as pd
import matplotlib.pyplot as plt
import os


def plot_data(df, title, xlabel, ylabel, min_value=None, max_value=None,
              specified_urls=None):
    plt.figure(figsize=(12, 6))

    # 定义线条样式和颜色
    line_styles = ['-', '--', '-.', ':']
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

    for idx, url in enumerate(df.columns[1:]):  # 跳过第一列（时间）
        # 如果指定了 URL 列表，则只绘制这些 URL
        if specified_urls is not None and url not in specified_urls:
            continue

        # 过滤数据
        filtered_data = df[(df[url] >= (
            min_value if min_value is not None else float('-inf'))) &
                           (df[url] <= (
                               max_value if max_value is not None else float(
                                   'inf')))]

        # 仅在过滤后的数据不为空时绘制
        if not filtered_data.empty:
            # 使用不同的线条样式和颜色
            plt.plot(filtered_data['minute_key'], filtered_data[url],
                     label=url,
                     linestyle=line_styles[idx % len(line_styles)],
                     color=colors[idx % len(colors)],
                     marker='o')  # 添加数据点标记

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.legend()  # 仅在有数据时显示图例
    plt.tight_layout()
    plt.show()


def visualize_statistics(output_dir, specified_urls=None):
    # 定义文件路径和过滤条件
    files = {
        # 'url_request_count.csv': (
        # 'url request count', 'time', 'count', 0, None),
        # 'url request count', 'time', 'count', 5000, None),
        # 'url_total_response_time.csv': ('每分钟总响应时间', 'time', '总响应时间 (毫秒)', 2000, None),  # 例如，最大值为 10000 毫秒
        # 'url_avg_response_time.csv': ('每分钟平均响应时间', 'time', '平均响应时间 (毫秒)', 0, None),  # 例如，最大值为 5000 毫秒
        'url_total_response_size.csv': ('url total response size', 'time', 'Bytes', 1000000, None),
        # 'url total response size', 'time', 'Bytes', 0, None),
        # 'url_avg_response_size.csv': ('每分钟平均响应大小', 'time', '平均响应大小 (字节)', 100000, None)  # 例如，最大值为 100000 字节
    }

    for file_name, (
    title, xlabel, ylabel, min_value, max_value) in files.items():
        file_path = os.path.join(output_dir, file_name)
        df = pd.read_csv(file_path)
        plot_data(df, title, xlabel, ylabel, min_value, max_value,
                  specified_urls)


def main():
    output_dir = 'url_statistics'  # 替换为您的输出目录
    # specified_urls = None # 替换为您想要展示的 URL 列表
    specified_urls = ["/v2/lib/filterrules"]  # 替换为您想要展示的 URL 列表
    visualize_statistics(output_dir, specified_urls)


if __name__ == "__main__":
    main()
