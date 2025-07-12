import matplotlib
matplotlib.use('Agg')  # 使用 Agg 后端
import matplotlib.pyplot as plt
import re
from datetime import datetime
from collections import defaultdict
import os
import pandas as pd
import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = b""
        for _ in range(100):
            chunk = f.read(1024)
            if not chunk:
                break
            raw_data += chunk
    result = chardet.detect(raw_data)
    return result['encoding']


def save_statistics(statistics_per_url, statistics_per_url_minute, output_prefix='processed_data'):
    with open(f'{output_prefix}_per_url.txt', 'w', encoding='utf-8') as f:
        for timestamp, url_stats in statistics_per_url.items():
            for url, stats in url_stats.items():
                f.write(f"{timestamp}\t{url}\t{stats['count']}\t{stats['total_time']}\t{stats['total_size']}\n")

    with open(f'{output_prefix}_per_url_minute.txt', 'w', encoding='utf-8') as f:
        for timestamp, url_stats in statistics_per_url_minute.items():
            for url, stats in url_stats.items():
                f.write(f"{timestamp}\t{url}\t{stats['count']}\t{stats['total_time']}\t{stats['total_size']}\n")


def visualize_statistics(statistics_per_url, statistics_per_url_minute):
    data = []
    for timestamp, url_stats in statistics_per_url_minute.items():
        for url, stats in url_stats.items():
            avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
            data.append({
                'Timestamp': timestamp,
                'URL': url,
                'Count': stats['count'],
                'Average Response Time': avg_time,
                'Total Size': stats['total_size']
            })

    df = pd.DataFrame(data)

    # 可视化请求次数
    plt.figure(figsize=(12, 6))
    for url in df['URL'].unique():
        url_data = df[df['URL'] == url]
        plt.plot(url_data['Timestamp'], url_data['Count'], marker='o', label=url)

    plt.title('Request Count per URL Over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Request Count')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    plt.savefig('request_count_per_url.png')
    plt.close()

    # 可视化平均响应时间
    plt.figure(figsize=(12, 6))
    for url in df['URL'].unique():
        url_data = df[df['URL'] == url]
        plt.plot(url_data['Timestamp'], url_data['Average Response Time'], marker='o', label=url)

    plt.title('Average Response Time per URL Over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Average Response Time (s)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    plt.savefig('average_response_time_per_url.png')
    plt.close()

    # 可视化总响应数据大小
    plt.figure(figsize=(12, 6))
    for url in df['URL'].unique():
        url_data = df[df['URL'] == url]
        plt.plot(url_data['Timestamp'], url_data['Total Size'], marker='o', label=url)

    plt.title('Total Response Size per URL Over Time')
    plt.xlabel('Timestamp')
    plt.ylabel('Total Response Size (bytes)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.2)
    plt.savefig('total_response_size_per_url.png')
    plt.close()


def parse_log_file(log_file_path, start_line=0, visualize_interval=100000):
    encoding = detect_encoding(log_file_path)

    statistics_per_url = defaultdict(lambda: defaultdict(lambda: {
        'count': 0,
        'total_time': 0.0,
        'total_size': 0
    }))
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

    try:
        with open(log_file_path, 'r', encoding='etf-8') as log_file:
            for _ in range(start_line):
                log_file.readline()

            for line_number, line in enumerate(log_file, start=start_line + 1):
                try:
                    match = log_pattern.search(line)

                    if match:
                        timestamp_str = match.group('timestamp')
                        timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S %z')
                        timestamp_second = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        timestamp_minute = timestamp.strftime('%Y-%m-%d %H:%M')

                        response_time = float(match.group('response_time'))
                        response_size = int(match.group('content_length'))

                        url = match.group('url').split('?')[0]
                        statistics_per_url[timestamp_second][url]['count'] += 1
                        statistics_per_url[timestamp_second][url]['total_time'] += response_time
                        statistics_per_url[timestamp_second][url]['total_size'] += response_size

                        statistics_per_url_minute[timestamp_minute][url]['count'] += 1
                        statistics_per_url_minute[timestamp_minute][url]['total_time'] += response_time
                        statistics_per_url_minute[timestamp_minute][url]['total_size'] += response_size

                        # 每处理一定数量的行就进行一次可视化
                        if line_number % visualize_interval == 0:
                            visualize_statistics(statistics_per_url, statistics_per_url_minute)

                except UnicodeDecodeError as e:
                    print(f"UnicodeDecodeError on line {line_number}: {e}. Skipping this line.")
                    continue  # 跳过当前行，继续处理下一行
                except Exception as e:
                    print(f"Error processing line {line_number}: {e}")
                    continue  # 跳过当前行，继续处理下一行

    except Exception as e:
        print(f"Error opening file: {e}")
        return statistics_per_url, statistics_per_url_minute

    return statistics_per_url, statistics_per_url_minute


def main():
    log_file_path = 'analysis-nginx-router-svc_04021619.log'
    checkpoint_file = 'checkpoint.txt'

    start_line = 0
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as cp_file:
            start_line = int(cp_file.read().strip())

    # 解析日志文件并逐步可视化
    statistics_per_url, statistics_per_url_minute = parse_log_file(log_file_path, start_line)

    # 最后一次可视化
    visualize_statistics(statistics_per_url, statistics_per_url_minute)

    print("Visualization has been generated.")


if __name__ == "__main__":
    main()
