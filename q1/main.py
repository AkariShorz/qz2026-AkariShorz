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