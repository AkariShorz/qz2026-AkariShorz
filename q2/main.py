# 用户信息存在 JSON 文件里，关掉程序再打开也能接着用
import json


# 用户按添加顺序放着，id 自动往上排，不会撞。
class UserManager:

    def __init__(self):
        # 先备好空列表，新用户的 id 从 1 开始排
        self._users = []
        self._next_user_id = 1