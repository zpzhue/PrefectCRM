import re


from django.shortcuts import HttpResponse, redirect, reverse
from django.utils.deprecation import MiddlewareMixin


class PermissionMiddleware(MiddlewareMixin):

    def process_request(self, request):

        if request.user and request.user.is_superuser:
            return None

        # 1. 获取请求的路径：
        current_path = request.path


        # 2. 放行白名单：
        white_list = ['/admin/', '/login/', '/register/', '/index/']
        for white_path in white_list:
            if re.search(white_path, current_path):
                return None

        # 3. 检测用户是否登陆：
        if not request.session.get('user_id'):
            return redirect(to=reverse('login'))

        # 4.1 获取用户的权限列表：
        permission_list = request.session.get('permission_list')
        for permission in permission_list:
            if re.search(f'^{permission.get("url")}$', current_path):
                return None

        return HttpResponse('您无权限访问此页面')