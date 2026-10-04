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

    # 找着了就改年龄，没找到就说调用方没改成
    def update_age(self, user_id, new_age):
        user = self.get_user(user_id)
        if user is None:
            return False

        user["age"] = new_age
        return True

    # 找到对应用户就删掉，最后说一声删没删成
    def remove_user(self, user_id):
        for index, user in enumerate(self._users):
            if user["id"] == user_id:
                del self._users[index]
                return True
        return False

    # 按原来的顺序给一份列表副本，并复制每个用户字典，避免外部修改影响内部数据
    def list_users(self):
        return [user.copy() for user in self._users]

    # 把现在这批用户存进 JSON 文件，中文也照样保留
    def save_to_json(self, filepath):
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(
            self._users,
            file,
                ensure_ascii=False,
                indent=2,
            )

    # 从文件里读回用户，直接替换当前这份列表
    def load_from_json(self, filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            users = json.load(file)

        # 文件读完再换列表；下次新增时，id 就从最大值后面接着排
        self._users = users
        max_id = max(
            (user["id"] for user in users),
            default=0,
        )
        self._next_user_id = max_id + 1
