# 将当前请求的用户放入上下文，供模型信号写审计记录时读取
from .signals import current_actor


class ActorContextMiddleware:
    def __init__(self, get_response):
        # Django 将下一个中间件或视图传入，供本中间件处理完请求后调用
        self.get_response = get_response

    def __call__(self, request):
        # 匿名访客没有登录身份，因此审计记录中的操作人设为 None
        actor = request.user if request.user.is_authenticated else None
        token = current_actor.set(actor)
        try:
            return self.get_response(request)
        finally:
            # 请求结束后恢复原上下文，避免不同请求之间串用操作人信息
            current_actor.reset(token)
