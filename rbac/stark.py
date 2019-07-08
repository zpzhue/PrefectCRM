import json

from django.urls import path
from django.shortcuts import render, redirect, reverse, HttpResponse

from . import models
from crm.models import User
from stark.service.sites import site, ModelStrak


class PermissionConfig(ModelStrak):
    list_display = ['title', 'url', 'type', 'parent']

    def extra_url(self):
        urlpatterns = [
            path('distribute/', self.permission_distribute),
        ]

        return urlpatterns

    def permission_distribute(self, request):
        user_id = request.GET.get('uid')
        role_id = request.GET.get('rid')
        user = User.objects.filter(id=user_id)

        if request.method == 'POST' and request.POST.get('post_type') == 'role':
            role_ste = request.POST.getlist('rid')
            user.first().role.set(role_ste)

        if request.method == 'POST' and request.POST.get('post_type') == 'permission':
            role = models.Role.objects.filter(id=role_id).first()
            if not role:
                return HttpResponse('用户不存在')
            post_permission_list = request.POST.getlist('permission_id')
            print(post_permission_list)
            per_set_temp = set()
            for per_id in post_permission_list:
                per_set_temp.add(per_id)
                temp = models.Permission.objects.get(id=per_id)
                while temp.parent:
                    per_set_temp.add(temp.parent.id)
                    temp = temp.parent
            role.permission.set(per_set_temp)

        user_list = User.objects.all()
        role_list = models.Role.objects.all()

        role_id_list = []
        permission_id_list = []
        all_permissions = list(models.Permission.objects.values())
        all_permissions_json = json.dumps(all_permissions, ensure_ascii=False)

        if user_id:
            role_id_list = user.first().role.all().values('pk')
            role_id_list = [ role['pk'] for role in role_id_list ]
            permission_id_list = User.objects.get(id=user_id).role.filter(permission__isnull=False).values('permission__pk').distinct()

        if role_id:
            permission_id_list = models.Role.objects.filter(id=role_id).filter(permission__isnull=False).values('permission__pk').distinct()

        permission_id_list = [permission['permission__pk'] for permission in permission_id_list] if permission_id_list else []

        contex = {
            'user_list': user_list,
            'role_list': role_list,
            'user_id': user_id,
            'role_id': role_id,
            'role_id_list': role_id_list,
            'permission_id_list': permission_id_list,
            'all_permissions': all_permissions,
            'all_permissions_json': all_permissions_json,
        }

        return render(request, 'rbac/permission_distribute.html', contex)


class RoleConfig(ModelStrak):
    def permission(self, obj=None, is_get_header=False):
        if is_get_header:
            return '权限'
        return '&nbsp;&nbsp;||&nbsp;&nbsp;'.join([i.title for i in obj.permission.all()])

    # permission.short_desc = '权限'
    list_display = ['name', permission]


site.register(models.Permission, PermissionConfig)
site.register(models.Role, RoleConfig)
