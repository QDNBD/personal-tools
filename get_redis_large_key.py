#!/usr/bin/python
# -*- coding: utf-8 -*-


# coding=utf-8
"""

使用方式：
source /matrix/profile
python redis_memory_usage.py
"""
import logging
import soapa_logging_v2

from scia.dao.redisdb import RedisDao



from easy_util.dao.redis_util import RedisUtil

soapa_logging_v2.simple_config("redis-memory-usage")
logger = logging.getLogger("redis-memory-usage")
SCAN_COUNT = 10000


class Redis(object):
    def __init__(self, scan_match):
        self.redis_cli  = RedisDao.get("redis.redis-ha",0, socket_timeout=50)
        self.redis_iter = self.redis_cli.scan_iter(match=scan_match, count=SCAN_COUNT)

    def get_next(self):
        if not self.redis_iter:
            raise StopIteration
        try:
            data = next(self.redis_iter)
        except StopIteration:
            raise StopIteration
        except Exception as err:
            logger.exception(err)
            raise StopIteration
        return data

    def __iter__(self):
        return self

    def next(self):
        return self.get_next()


def get_redis_memory_usage():
    redis_obj = Redis("*")
    key_count_map = dict()
    key_memory_map = dict()
    count = long()
    for key in redis_obj.redis_iter:
        try:
            count += 1
            memory_use = redis_obj.redis_cli.execute_command("MEMORY USAGE", key)
            key_memory_map[key] = memory_use
        except Exception as e:
            logger.exception("key: {}, err: {}".format(key, e))

    # 按内存使用量降序排序
    sorted_items = sorted(key_memory_map.items(), key=lambda x: x[1], reverse=True)


    print "Top 10 keys by memory usage:"
    for i in range(10):
        if i < len(sorted_items):
            key, memory = sorted_items[i]
            print key, format_size(memory)
        else:
            break


def format_size(size_bytes):
    """将字节转换为 KB/MB/GB 等单位，保留两位小数"""
    if size_bytes < 1024:
        return "%d B" % size_bytes
    elif size_bytes < 1024**2:
        return "%.2f KB" % (size_bytes / 1024.0)
    elif size_bytes < 1024**3:
        return "%.2f MB" % (size_bytes / (1024.0**2))
    elif size_bytes < 1024**4:
        return "%.2f GB" % (size_bytes / (1024.0**3))
    else:
        return "%.2f TB" % (size_bytes / (1024.0**4))


if __name__ == '__main__':
    get_redis_memory_usage()