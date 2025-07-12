#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime
from collections import defaultdict
import os
import csv

def parse_log_file(log_file_path, start_line=0):
    # 存储统计数据
    statistics_per_minute = defaultdict(lambda: defaultdict(lambda: {
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
    with open(log_file_path, 'r', encoding='utf-8') as log_file:
        # 跳过已处理的行
        for _ in range(start_line):
            log_file.readline()

        minute_key_ = None
        for line_number, line in enumerate(log_file, start=start_line + 1):
            # print(f"Processing line {line_number}: {line.strip()}")  # 打印当前行
            match = log_pattern.search(line)

            if match:
                timestamp = match.group('timestamp')
                url = match.group('url').split('?')[0]  # 截取问号之前的部分
                response_time = float(match.group('response_time'))
                response_size = int(match.group('content_length'))

                # 解析时间并按分钟分组
                minute_key = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S %z').strftime('%Y-%m-%d %H:%M')
                if minute_key_ is None:
                    minute_key_ = minute_key
                if minute_key == minute_key_:
                    # 更新统计数据
                    statistics_per_minute[minute_key][url]['count'] += 1
                    statistics_per_minute[minute_key][url]['total_time'] += response_time
                    statistics_per_minute[minute_key][url]['total_size'] += response_size
                else:
                    write_statistics_to_csv(statistics_per_minute, 'url_statistics')
                    statistics_per_minute.clear()  # 清空统计数据以便重新统计
                    break
                # print(f"Matched URL: {url}, Minute: {minute_key}, Response Time: {response_time}, Response Size: {response_size}")

                # 每分钟结束时写入统计结果
                # if line_number % 1000 == 0:  # 这里可以根据需要调整
                #     write_statistics_to_csv(statistics_per_minute, 'url_statistics')
                #     statistics_per_minute.clear()  # 清空统计数据以便重新统计
                #     break

    return statistics_per_minute, line_number


def write_statistics_to_csv(statistics_per_minute, output_dir):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    # print(f"Output directory '{output_dir}' has been created or already exists.")

    # 存储所有的 URL 和时间
    all_urls = set()
    all_minutes = set()

    # 首先收集所有的 URL 和时间
    for minute, urls in statistics_per_minute.items():
        all_minutes.add(minute)
        for url in urls.keys():
            all_urls.add(url)

    all_minutes = sorted(all_minutes)  # 排序时间
    all_urls = sorted(all_urls)  # 排序 URL

    # 创建请求次数表格
    count_file_path = os.path.join(output_dir, 'url_request_count.csv')
    with open(count_file_path, 'a', newline='', encoding='utf-8') as count_file:
        count_writer = csv.writer(count_file)

        # 写入表头
        if count_file.tell() == 0:  # 如果文件为空，写入表头
            count_writer.writerow(['URL'] + all_minutes)

        # 写入每个 URL 的请求次数
        for url in all_urls:
            row = [url]
            for minute in all_minutes:
                row.append(statistics_per_minute[minute][url]['count'] if url in statistics_per_minute[minute] else 0)
            count_writer.writerow(row)

    # 创建总响应时间表格
    time_file_path = os.path.join(output_dir, 'url_total_response_time.csv')
    with open(time_file_path, 'a', newline='', encoding='utf-8') as time_file:
        time_writer = csv.writer(time_file)

        # 写入表头
        if time_file.tell() == 0:  # 如果文件为空，写入表头
            time_writer.writerow(['URL'] + all_minutes)

        # 写入每个 URL 的总响应时间
        for url in all_urls:
            row = [url]
            for minute in all_minutes:
                avg_time = (statistics_per_minute[minute][url]['total_time'] / statistics_per_minute[minute][url]['count']
                            if url in statistics_per_minute[minute] and statistics_per_minute[minute][url]['count'] > 0 else 0)
                row.append(avg_time)
            time_writer.writerow(row)

    # 创建总响应大小表格
    size_file_path = os.path.join(output_dir, 'url_total_response_size.csv')
    with open(size_file_path, 'a', newline='', encoding='utf-8') as size_file:
        size_writer = csv.writer(size_file)

        # 写入表头
        if size_file.tell() == 0:  # 如果文件为空，写入表头
            size_writer.writerow(['URL'] + all_minutes)

        # 写入每个 URL 的总响应大小
        for url in all_urls:
            row = [url]
            for minute in all_minutes:
                row.append(statistics_per_minute[minute][url]['total_size'] if url in statistics_per_minute[minute] else 0)
            size_writer.writerow(row)


def main():
    log_file_path = 'analysis-nginx-router-svc_04021619.log'
    output_dir = 'url_statistics'
    checkpoint_file = 'checkpoint.txt'  # 这里是相对路径，默认在当前目录

    # 读取上次处理的行号
    start_line = 0
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as cp_file:
            start_line = int(cp_file.read().strip())

    # 解析日志文件
    statistics_per_minute, last_line = parse_log_file(log_file_path, start_line)

    # 更新检查点文件
    with open(checkpoint_file, 'w', encoding='utf-8') as cp_file:
        cp_file.write(str(last_line))

    print(f"Statistics have been written to '{output_dir}' directory.")


if __name__ == "__main__":
    main()
