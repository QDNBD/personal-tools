#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from scia.dao.mongodb import MgoClientDao
from collections import defaultdict
mongo_tioc_client = MgoClientDao(target="mongo.mongo-tim")
db = mongo_tioc_client["db_unknown_intelligence"]
stats = db.command("collstats", "tb_top_visit_host_info")


# 打印详细信息
print "name: %s" % stats["ns"]
print "count: %d" % stats["count"]
print "size: %.2f MB" % (stats["size"] / (1024 * 1024))
print "totalIndexSize: %.2f MB" % (stats["totalIndexSize"] / (1024 * 1024))
print "storageSize: %.2f MB" % (stats["storageSize"] / (1024 * 1024))
print "avgObjSize: %.2f KB" % (stats["avgObjSize"] / 1024)