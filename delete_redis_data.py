#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import soapa_logging_v2
from scia.dao.redisdb import RedisDao

soapa_logging_v2.simple_config("redis-delete-key-ti-cluster")
logger = logging.getLogger("redis-delete-key-ti-cluster")
SCAN_COUNT = 1000


def safe_delete_keys(redis_cli, pattern):
    i = long()
    max_retries = 3
    try:
        for key in redis_cli.scan_iter(match=pattern, count=SCAN_COUNT):
            if i % 100000 == 0:
                logger.info("del count: {}, del key: {}".format(i, key))

            print key  # 打印找到的键
            # 尝试删除键，带重试机制
            retries = 0

            while retries < max_retries:
                try:
                    # redis_cli.delete(key)
                    i += 1
                    break  # 成功删除后跳出重试循环
                except Exception as e:
                    retries += 1
                    logger.warning("删除键时发生错误: {}，重试次数: {}".format(e, retries))
                    if retries == max_retries:
                        logger.info("达到最大重试次数，跳过键: {}".format(key))
	
            if i % 1000 == 0:
                logger.info("退出")
                break
    except Exception as e:
        logger.error("发生错误: {}".format(e))
    finally:
        logger.info("总共找到的键数量: {}".format(i))


if __name__ == "__main__":
    # 连接到 Redis 集群
    ts = time.time()
    # redis_cli = RedisDao.get(target="redis.redis-nta-mdp-cluster", db=0,
    #                          socket_timeout=5)
    redis_cli = RedisDao.get(target="redis.redis-ti-cluster-de", db=0,
                             socket_timeout=5)
    safe_delete_keys(redis_cli, '*')
    logger.info("del all time seconds: {}".format(time.time() - ts))
