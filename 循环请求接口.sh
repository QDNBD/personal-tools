#!/bin/bash

# 定义请求的 URL 和数据
URL="https://121.32.254.180/v2/analysis/ip/reputation?_method=GET&token=377418215c4a2da7416c2a47e4495d87a148a1f8c14f734a6df89cbeda87ed6b"
DATA='{
    "ipsInfo": [{"ip":"143.92.57.121", "direction": 2, "port": 7121}],
    "deviceId": "DB3EF0D2",
    "deviceVersion": "v1.0.0",
    "source": "NGAF"
}'

# 日志文件
LOG_FILE="curl_requests.log"

# 清空日志文件
> "$LOG_FILE"

# 循环执行 100 次
for i in {1..100}
do
    echo "Executing request #$i" >> "$LOG_FILE"
    { time curl -X POST "$URL" -H "Content-Type: application/json" -d "$DATA" --max-time 60 --insecure; } 2>> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"
done

echo "All requests completed. Check the log file: $LOG_FILE"