#!/usr/bin/env python3
# Django 的命令行入口；数据库迁移和启动服务等命令都从这里执行
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "article_manager.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
