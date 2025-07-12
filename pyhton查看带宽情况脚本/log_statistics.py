#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime
from collections import defaultdict
import os


def parse_log_file(log_file_path, start_line=0):
    # 存储统计数据
    statistics_per_url = defaultdict(lambda: defaultdict(lambda: {
        'count': 0,
        'total_time': 0.0,
        'total_size': 0
    }))

    # 存储按分钟统计的数据
    statistics_per_url_minute = defaultdict(lambda: defaultdict(lambda: {
        'count': 0,
        'total_time': 0.0,
        'total_size': 0
    }))

    log_pattern = re.compile(
        r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] '
        r'(?P<processing_time>\d+) (?P<response_time>\d+\.\d+) '
        r'"(?P<method>\w+) (?P<url>.*?) HTTP/[\d\.]+" (?P<status_code>\d+) (?P<content_length>\d+) '
        r'.*? (?P<time_taken>\d+\.\d+)'
    )

    # 读取日志文件
    with open(log_file_path, 'r') as log_file:
        # 跳过已处理的行
        for _ in range(start_line):
            log_file.readline()

        for line_number, line in enumerate(log_file, start=start_line + 1):
            match = log_pattern.search(line)

            if match:
                # 截取问号之前的部分
                url = match.group('url').split('?')[0]

                # 获取时间戳并格式化为秒和分钟
                timestamp_str = match.group('timestamp')
                timestamp = datetime.strptime(timestamp_str,
                                              '%d/%b/%Y:%H:%M:%S %z')
                timestamp_second = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                timestamp_minute = timestamp.strftime('%Y-%m-%d %H:%M')

                # 更新统计数据
                response_time = float(match.group('response_time'))
                response_size = int(match.group('content_length'))

                # 按秒统计
                statistics_per_url[timestamp_second][url]['count'] += 1
                statistics_per_url[timestamp_second][url][
                    'total_time'] += response_time
                statistics_per_url[timestamp_second][url][
                    'total_size'] += response_size

                # 按分钟统计
                statistics_per_url_minute[timestamp_minute][url]['count'] += 1
                statistics_per_url_minute[timestamp_minute][url][
                    'total_time'] += response_time
                statistics_per_url_minute[timestamp_minute][url][
                    'total_size'] += response_size

            else:
                print("No match found.")
                continue  # 如果没有匹配，跳过当前循环

            if line_number % 100000 == 0:
                write_statistics_to_files(statistics_per_url, 'url_statistics',
                                          'second')
                write_statistics_to_files(statistics_per_url_minute,
                                          'url_statistics', 'minute')

                statistics_per_url.clear()  # 清空统计数据以便重新统计

    return statistics_per_url, statistics_per_url_minute, line_number


def write_statistics_to_files(statistics_per_url, output_dir, time_frame):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 将每个 URL 的统计结果写入不同的文件
    for timestamp, url_stats in statistics_per_url.items():
        for url, stats in url_stats.items():
            # 生成文件名
            url_filename = url.replace('/', '_').replace('?',
                                                         '_') + f'_{time_frame}.txt'
            url_file_path = os.path.join(output_dir, url_filename)

            with open(url_file_path, 'a') as output_file:  # 使用 'a' 模式追加写入
                output_file.write(
                    f"Statistics for URL: {url} at {timestamp}\n")
                output_file.write(f"Total Count: {stats['count']}\n")
                avg_time = stats['total_time'] / stats['count'] if stats[
                                                                       'count'] > 0 else 0
                output_file.write(f"Average Response Time: {avg_time:.3f}s\n")
                output_file.write(
                    f"Total Response Size: {stats['total_size']} bytes\n")


def main():
    log_file_path = 'analysis-nginx-router-svc_04021619.log'
    output_dir = 'url_statistics'
    checkpoint_file = 'checkpoint.txt'  # 这里是相对路径，默认在当前目录

    # 读取上次处理的行号
    start_line = 0
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as cp_file:
            start_line = int(cp_file.read().strip())

    # 解析日志文件
    statistics_per_url, statistics_per_url_minute, last_line = parse_log_file(
        log_file_path, start_line)

    # 更新检查点文件
    with open(checkpoint_file, 'w') as cp_file:
        cp_file.write(str(last_line))

    print(f"Statistics have been written to '{output_dir}' directory.")


if __name__ == "__main__":
    main()
