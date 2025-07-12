#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
mogno插入随机数据

使用方式：
# 插入1万条数据（每批500条），content字段每条2KB：
python insert_data.py -t 10000 -b 500 -s 2048

# 插入50万条数据，每批1000条（大数据量测试）：
python insert_data.py -t 500000 -b 1000 -s 5120
"""

from pymongo import InsertOne
from scia.dao.mongodb import MgoCollectionDao
import time
import logging
import soapa_logging_v2
import argparse
import random
import string
import uuid

soapa_logging_v2.simple_config("data_loader")
logger = logging.getLogger("data_loader")

def get_time_ms():
    return int(time.time() * 1000)

class DataInjector:
    """配置化MongoDB数据插入类"""
    def __init__(self, total, batch, data_size):
        self.total_count = total
        self.batch_size = batch
        self.data_size = data_size
        self.collection = MgoCollectionDao(
            target="mongo.mongo-tim-de",
            db_name="db_fc_hashinfo",
            collection_name="tb_fc_hashinfo"
        )

    def _generate_document(self, idx):
        # Generate a random string with length equal to self.data_size
        content = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(self.data_size))
        
        return {
            "id": idx,
            "file_md5": uuid.uuid4().hex,
            "content": content,
            "timestamp": get_time_ms(),
            "tags": ["test"]
        }

    def _gen_batch(self):
        for start in range(0, self.total_count, self.batch_size):
            end = start + self.batch_size
            docs = [self._generate_document(i) for i in range(start, end)]
            yield docs

    def execute(self):
        """执行批量插入"""
        success = 0
        failed = 0

        for batch in self._gen_batch():
            ops = [InsertOne(doc) for doc in batch]

            try:
                res = self.collection.bulk_write(ops)
                success += len(ops)
            except Exception as e:
                logger.error("批量插入失败: %s" % str(e))
                failed += len(ops)

            logger.info("完成: %d/%d" % (success, self.total_count))

        logger.info("插入完成 | 成功: %d | 失败: %d" % (success, failed))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--total", type=int, default=10000,
                        help="总数据量，默认10000")
    parser.add_argument("-b", "--batch", type=int, default=500,
                        help="批量大小，默认500")
    parser.add_argument("-s", "--size", type=int, default=256,
                        help="每个文档content字段的大小（字节），默认256B")
    args = parser.parse_args()

    # 执行插入操作
    loader = DataInjector(
        total=args.total,
        batch=args.batch,
        data_size=args.size
    )
    loader.execute()