import argparse
import json
#先引入必要的模块

# 逐行读取 JSONL 日志，坏行直接跳，最后返回汇总结果就ok
def analyze_log(file_path: str) -> dict:
    stats = {
        "total": 0,
        "by_level": {},
        "by_user": {},
        "last_error": None,
    }#先准备一个空的统计结果

    try:
        file = open(file_path, "r", encoding="utf-8")#让我们说中文
    except FileNotFoundError:
        # 路径不存在时返回空统计就行，别让程序给报错退出了
        return stats

    with file:
        for line in file:#逐条处理，没必要一次把整个文件都放进内存
            pass