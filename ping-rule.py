#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import time

# url = "http://filemanage-proxy-golang-svc-master.update.svc.cluster.local:8002/v1/downloads/update"
url = "https://upd.sangfor.com.cn/v1/downloads/update"
# url = "http://localhost:8000/v1/downloads/update"
# url = "http://localhost:8002/v1/downloads/update"
# url = "http://filemanage-proxy-master.update.svc.cluster.local:8000/v1/downloads/update"
# url = "https://upd.sangfor.com/v1/downloads/update"
# url = "https://upd.forenova.com/v1/downloads/update"
headers = {
    'Content-Type': 'application/json'
}

payload = {
    "source": "EDR",
    "deviceVersion": "3.5.24.1436",
    "deviceId": "36417444460",
    "meta": {
        "packageType": "vdb"
    },
    "area": "CN"
}

def send_request():
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload,verify=False)
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒

        if response.status_code == 200:
            print("成功: 200 (响应时间: {:.2f}毫秒)".format(response_time))
            return response_time
        else:
            print("失败: 状态码 {} (响应时间: {:.2f}毫秒)".format(response.status_code, response_time))
            return response_time

    except requests.exceptions.RequestException as e:
        print("请求错误: {}".format(e))
        return None

if __name__ == "__main__":
    # 设置拨测次数
    test_count = 100
    total_time = 0
    timeout_count = 0
    timeout_threshold = 10 * 1000  # 设置超时阈值为5000毫秒

    for i in range(test_count):
        print("第 {} 次拨测:".format(i + 1))
        response_time = send_request()

        if response_time is not None:
            total_time += response_time
            if response_time > timeout_threshold:
                print("警告!!!!!: 第 {} 次请求超时 (响应时间: {:.2f}毫秒)".format(i + 1, response_time))
                timeout_count += 1
        else:
            timeout_count += 1

        time.sleep(1)  # 每次请求之间的间隔

    # 计算平均耗时
    average_time = total_time / (test_count - timeout_count) if (test_count - timeout_count) > 0 else 0
    print("平均响应时间: {:.2f}毫秒".format(average_time))
    print("超时请求总数: {}".format(timeout_count))