# coding=utf-8

"""
使用方式：
source /matrix/profile
python redis_memory_usage.py dnslib:* &
"""

import time
import logging
import soapa_logging_v2
from easy_util.dao.redis_util import RedisUtil
from concurrent.futures import ThreadPoolExecutor, as_completed

soapa_logging_v2.simple_config("redis-memory-usage-nta")
logger = logging.getLogger("redis-memory-usage-nta")

SCAN_COUNT = 10000
THREAD_COUNT = 8  # 设置线程数量


class Redis(object):
    def __init__(self, scan_match):
        self.redis_cli = RedisUtil.get_redis_cluster_nta_mdp_db(
            socket_timeout=50)
        self.redis_iter = self.redis_cli.scan_iter(match=scan_match,
                                                   count=SCAN_COUNT)

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


def process_keys(redis_obj, keys):
    key_count_map = dict()
    key_memory_map = dict()
    for key in keys:
        try:
            memory_use = redis_obj.redis_cli.execute_command("MEMORY USAGE",
                                                             key)

            # 获取前缀，获取前两部分
            arr = key.split(":")
            if len(arr) >= 2:
                prefix = "".join([arr[0], ":", arr[1]])
            elif len(arr) == 1:
                prefix = arr[0]
            else:
                continue

            # 数量累加
            key_count_map[prefix] = key_count_map.get(prefix, 0) + 1

            # 所需内存累加
            key_memory_map[prefix] = key_memory_map.get(prefix, 0) + memory_use

        except Exception as e:
            logger.exception("key: {}, err: {}".format(key, e))

    return key_count_map, key_memory_map


def get_redis_memory_usage():
    redis_obj = Redis("*")
    count = 0
    futures = []
    key_count_map_total = dict()
    key_memory_map_total = dict()

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        while True:
            keys = []
            try:
                for _ in range(SCAN_COUNT):
                    keys.append(next(redis_obj.redis_iter))
            except StopIteration:
                break

            count += len(keys)

            # 直接处理当前批次的键
            futures.append(executor.submit(process_keys, redis_obj, keys))

            for future in as_completed(futures):
                key_count_map, key_memory_map = future.result()
                for prefix, count_ in key_count_map.items():
                    key_count_map_total[prefix] = key_count_map_total.get(
                        prefix, 0) + count_
                for prefix, memory_ in key_memory_map.items():
                    key_memory_map_total[prefix] = key_memory_map_total.get(
                        prefix, 0) + memory_

            # 每100000个键打印一次当前的键计数和内存使用情况
            if count % 100000 == 0:
                logger.info(
                    "scan count: {}, key_count_map: {}, key_memory_map: {}".format(
                        count,
                        key_count_map_total,
                        key_memory_map_total))

    logger.info(
        "total scan count: {}, key_count_map: {}, key_memory_map: {}".format(
            count,
            key_count_map_total,
            key_memory_map_total))
    return count, key_count_map_total, key_memory_map_total


if __name__ == '__main__':
    ts = time.time()
    total_count, key_count_map_, key_memory_map_ = get_redis_memory_usage()
    logger.info(
        "total scan count: {}, key_count_map: {}, key_memory_map: {}".format(
            total_count,
            key_count_map_,
            key_memory_map_))
    logger.info("del all time seconds: {}".format(time.time() - ts))
