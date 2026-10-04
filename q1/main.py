# 统计 JSON Lines 日志文件中的级别、用户和最后一条错误
import argparse
import json


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
            try:
                record = json.loads(line) #json string  python dict
            except json.JSONDecodeError:
                # JSONL 一行一条记录，某行损坏不影响后面正常输出日志
                continue

            if not isinstance(record, dict):
                continue

            # 保证正常日志得包含这四个字段；缺字段的记录跟坏行坐一桌，跳过
            try:
                level = record["level"]
                user = record["user"]
                message = record["message"]
            except KeyError:
                continue

            stats["total"] += 1
            stats["by_level"][level] = stats["by_level"].get(level, 0) + 1
            stats["by_user"][user] = stats["by_user"].get(user, 0) + 1

            if level == "ERROR":
                # 文件是顺序读取的，最后一次赋值即最后一条错误日志
                stats["last_error"] = message

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="统计 JSON Lines 格式的日志")
    parser.add_argument("filepath", nargs="?", default="app.jsonl", help="待分析的 .jsonl 文件路径")
    args = parser.parse_args()
    print(json.dumps(analyze_log(args.filepath), ensure_ascii=False, indent=2))
