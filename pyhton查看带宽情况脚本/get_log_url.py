#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime


def parse_log_file(log_file_path, url_filter=None, start_time=None,
                   end_time=None, output_file_path='filtered_log.log'):
    log_pattern = re.compile(
        r'(?P<ip>[\d\.]+) - - \[(?P<timestamp>[^\]]+)\] '
        r'(?P<processing_time>\d+) (?P<response_time>\d+\.\d+) '
        r'"(?P<method>\w+) (?P<url>.*?) HTTP/[\d\.]+" (?P<status_code>\d+) (?P<content_length>\d+) '
        r'.*? (?P<time_taken>\d+\.\d+)'
    )

    # 创建输出文件
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        # 读取日志文件
        with open(log_file_path, 'r', encoding='utf-8') as log_file:
            # 跳过已处理的行
            start_line = 2000000
            for _ in range(start_line):
                log_file.readline()

            for _, line in enumerate(log_file, start=start_line + 1):
                match = log_pattern.search(line)

                if match:
                    timestamp = match.group('timestamp')
                    url_ = match.group('url').split('?')[0]
                    url = re.sub(r'/[a-fA-F0-9]{32}$', '', url_)
                    content_length = int(match.group('content_length'))
                    log_time = datetime.strptime(timestamp,
                                                 '%d/%b/%Y:%H:%M:%S %z')

                    # 检查 URL 过滤
                    if url_filter and url not in url_filter:
                        continue

                    # 检查时间范围过滤
                    if start_time and log_time < start_time:
                        continue
                    if end_time and log_time > end_time:
                        break

                    if content_length < 10000:
                        continue

                    # 写入满足条件的行
                    output_file.write(line)

    print(f"Filtered logs have been written to '{output_file_path}'.")


def main():
    log_file_path = 'analysis-nginx-router-svc_04071640.log'
    output_file_path = 'get_filtered_log_04071640.log'

    # 指定需要过滤的 URL 列表
    url_filter = ['/v2/lib/filterrules']  # 示例 URL 列表
    # start_time = None  # 示例开始时间，可以设置为 None
    # end_time = None  # 示例结束时间，可以设置为 None
    start_time = datetime.strptime('2025-04-07 16:57:00 +0800',
                                   '%Y-%m-%d %H:%M:%S %z')  # 示例开始时间
    end_time = datetime.strptime('2025-04-07 17:12:00 +0800',
                                 '%Y-%m-%d %H:%M:%S %z')  # 示例结束时间

    # 解析日志文件并写入过滤后的结果
    parse_log_file(log_file_path, url_filter, start_time, end_time,
                   output_file_path)


if __name__ == "__main__":
    main()
