# coding=utf-8
"""
使用方式：
source /matrix/profile
python redis_memory_usage.py
"""
import logging
import soapa_logging_v2
from easy_util.dao.redis_util import RedisUtil

soapa_logging_v2.simple_config("redis-memory-usage-nta")
logger = logging.getLogger("redis-memory-usage-nta")
SCAN_COUNT = 10000


class Redis(object):
    def __init__(self, scan_match):
        # self.redis_cli = RedisUtil.get_redis_mq_db(db=11, socket_timeout=5)
        self.redis_cli = RedisUtil.get_redis_cluster_nta_mdp_db(socket_timeout=50)
        # self.redis_cli = RedisUtil.get_redis_cluster_ti_db(socket_timeout=5)
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


def format_memory_size(size):
    """将字节转换为更易读的格式（B、KB、MB、GB）。"""
    if size < 1024:
        return "{} B".format(size)
    elif size < 1024 ** 2:
        return "{:.2f} KB".format(size / 1024.0)
    elif size < 1024 ** 3:
        return "{:.2f} MB".format(size / (1024.0 ** 2))
    else:
        return "{:.2f} GB".format(size / (1024.0 ** 3))


def get_redis_memory_usage():
    redis_obj = Redis("*")
    key_count_map = dict()
    key_memory_map = dict()
    count = long()
    for key in redis_obj.redis_iter:
        try:
            count += 1
            memory_use = redis_obj.redis_cli.execute_command("MEMORY USAGE",
                                                             key)
            if memory_use is None:
                logger.warning("Memory usage for key {} is None".format(key))
                continue
            # 获取前缀
            arr = key.split(":")
            if len(arr) >= 1:
                prefix = arr[0]
            else:
                continue
            # 数量累加
            if prefix in key_count_map:
                key_count_map[prefix] += 1
            else:
                key_count_map[prefix] = 1
            # 所需内存累加
            if prefix in key_memory_map:
                key_memory_map[prefix] += memory_use
            else:
                key_memory_map[prefix] = memory_use
            if count % 100000 == 0:
                logger.info(
                    "scan count: {}, key_count_map: {}, key_memory_map: {}".format(
                        count,
                        key_count_map,
                        key_memory_map))
        except Exception as e:
            logger.exception("key: {}, err: {}".format(key, e))
    return count, key_count_map, key_memory_map


if __name__ == '__main__':
    total_count, key_count_map_, key_memory_map_ = get_redis_memory_usage()
    logger.info(
        "total scan count: {}, key_count_map: {}, key_memory_map: {}".format(
            total_count,
            key_count_map_,
            key_memory_map_))
