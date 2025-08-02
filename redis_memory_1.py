# coding=utf-8

"""
使用方式：
source /matrix/profile
python redis_memory_usage.py dnslib:* &
"""

import logging
import soapa_logging_v2
from easy_util.dao.redis_util import RedisUtil
from scia.dao.redisdb import RedisDao

soapa_logging_v2.simple_config("redis-memory-usage-")
logger = logging.getLogger("redis-memory-usage-")

SCAN_COUNT = 10000


class Redis(object):
    def __init__(self, scan_match):
        # self.redis_cli = RedisUtil.get_redis_cluster_ti_db(socket_timeout=5)
        # self.redis_cli = RedisUtil.get_redis_cluster_nta_mdp_db(socket_timeout=50)
        self.redis_cli = RedisUtil.get_redis_ha_mul_db(db=3, socket_timeout=50)
        # self.redis_cli = RedisDao.get(target="redis.redis-ha", db=db,
        #                               socket_timeout=50,
        #                               **connection_kwargs)
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

            # 获取前缀，获取前两部分 TODO 根据需要更改以下获取前缀的代码
            arr = key.split(":")
            if len(arr) >= 2:
                prefix = "".join([arr[0], ":", arr[1]])
            elif len(arr) == 1:
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
