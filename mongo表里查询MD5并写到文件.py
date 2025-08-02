#!/usr/bin/python
# -*- coding: utf-8 -*-


from scia.dao.mongodb import MgoCollectionDao
import time

def get_file_info_by_day():
    from bson.objectid import ObjectId
    from datetime import datetime, timedelta

    col = MgoCollectionDao("mongo.mongo-file-storage-shard", "db_filestorage_info", "tb_filestorage_info")
    # 设置日期范围
    start_date = datetime(2025, 5, 22,21,30,00)  # 开始日期
    end_date = datetime(2025, 5, 23,3,30,00)  # 结束日期
    # 目标数据量
    target_count = 50000000
    current_count = 0
    num_map ={}
    size_map = {}

    # 打开文件写入
    with open("/matrix/data/file_info", "w") as f:
        # 遍历日期范围
        current_date = start_date
        while current_date <= end_date and current_count < target_count:
            # 计算下一个日期
            next_date = current_date + timedelta(days=1)

            # 创建 ObjectId 范围
            start_id = ObjectId.from_datetime(current_date)
            end_id = ObjectId.from_datetime(next_date)
            # 设置 _id 范围的查询条件
            query = {
                "_id": {
                    "$gte": start_id,
                    "$lt": end_id
                }
            }
            # 查询数据
            cursor = col.find(query, {"_id": 0, "business": 1,"file_size":1 ,"source":1})
            # 处理查询结果
            for item in cursor:
                business = item.get("business","未知")
                file_size = item.get("file_size",0)
                source = item.get("source","未知")
                file_md5 = item.get("file_md5","未知")
                f.write("{},{},{},{}\n".format(file_md5,business,file_size,source))
                num_map[source] = num_map.get(source,0)+1
                size_map[source] = size_map.get(source,0)+file_size
            # 更新日期
            current_date = next_date
            print current_date
        # 输出数量

        for k,v in num_map.items():
            print  k,v
        print  "num_map--"
        for k,v in size_map.items():
            print k,v








def get_file_info():
    col = MgoCollectionDao("mongo.mongo-tim", "db_fc_hashinfo", "tb_fc_hashinfo")
    cursor = col.find({}, {"_id": 0, "file_md5": 1})
    i = 0
    with open("file_md5", "w") as f:
        for item in cursor:
            i += 1
            if i == 500000:
                cursor.close()
                break
            md5 = item.get("file_md5")
            if not md5:
                continue
            f.write("{}\n".format(md5))
            


#!/usr/bin/python
# -*- coding: utf-8 -*-


from scia.dao.mongodb import MgoCollectionDao
import time   

def find_by_day():
    from bson.objectid import ObjectId
    from datetime import datetime, timedelta

    col = MgoCollectionDao("mongo.mongo-filecloud", "vt_sample_report", "tb_vt_sample_report")
    # 设置日期范围
    start_date = datetime(2025, 7, 14)  # 开始日期
    end_date = datetime(2025, 7, 16)  # 结束日期

    # 目标数据量
    target_count = 50
    current_count = 0

    # 打开文件写入
    with open("file_md5", "w") as f:
        # 遍历日期范围
        current_date = start_date
        while current_date <= end_date and current_count < target_count:
            # 计算下一个日期
            next_date = current_date + timedelta(days=1)

            # 创建 ObjectId 范围
            start_id = ObjectId.from_datetime(current_date)
            end_id = ObjectId.from_datetime(next_date)
            # 设置 _id 范围的查询条件
            query = {
                "_id": {
                    "$gte": start_id,
                    "$lt": end_id
                }
            }

            # 查询数据
            cursor = col.find(query, {"_id": 0, "md5": 1}).limit(10)
            # 处理查询结果
            for item in cursor:
                md5_ = item.get("md5")
                if not md5_:
                    continue
                f.write("{}\n".format(md5_))
                current_count += 1
                if current_count >= target_count:
                    return

            # 更新日期
            current_date = next_date



if __name__ == '__main__':
    ts= time.time()
    find_by_day()
    print time.time()-ts
