# 用户信息存在 JSON 文件里，关掉程序再打开也能接着用
import json


# 用户按添加顺序放着，id 自动往上排，不会撞。
class UserManager:

    def __init__(self):
        # 先备好空列表，新用户的 id 从 1 开始排
        self._users = []
        self._next_user_id = 1
    
    # 把新用户装进字典放进列表，id 用完就往上 +1
    def add_user(self, name, age):
        user = {
            "id": self._next_user_id,
            "name": name,
            "age": age,
        }
        self._users.append(user)
        self._next_user_id += 1
        return user

    # 挨个按 id 找，找不到回个 None 就行
    def get_user(self, user_id):
        for user in self._users:
            if user["id"] == user_id:
                return user
        return None