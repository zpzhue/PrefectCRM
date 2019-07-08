import re
import json
import pprint
from django import template
from rbac import models
from functools import wraps

register = template.Library()

def get_timer(fn):
    @wraps(fn)
    def wrapper(*args):
        import time
        now = time.time()
        ret = fn(*args)
        print(fn.__name__, '执行时间为：', time.time()-now)
        return ret
    return wrapper

@get_timer
def get_nodes(permission_list, node_set):
    per_list = [per['url'] for per in permission_list]
    def inner(node_set):
        ret = []
        for node in node_set:
            node_data = {}
            if (node.url is not None) and (node.url not in per_list):continue
            node_data['text'] = node.title
            node_data['href'] = node.url or 'null'
            childe_set = node.permission_set.all()
            node_data['tags'] = childe_set.count()

            if node_data['tags'] > 0:
                node_data['nodes'] = inner(childe_set)
            ret.append(node_data)
        return ret
    return inner(node_set)


def get_nodes_g(request):
    permission_list = [per for per in request.session.get('permission_list') if per.get('type') == 'menu']
    node_set = models.Permission.objects.filter(parent_id=None, type='menu')
    per_list = [per['url'] for per in permission_list]

    def inner(node_set):
        for node in node_set:
            node_data = {}
            if (node.url is not None) and (node.url not in per_list):continue
            node_data['text'] = node.title
            node_data['href'] = node.url or '#'
            if node.url == request.path:
                node_data['state'] = {'expanded': True}
            childe_set = node.permission_set.all()
            node_data['tags'] = childe_set.count()

            if node_data['tags'] > 0:
                node_data['nodes'] = [g for g in inner(childe_set)]
                for node in node_data['nodes']:
                    if node.get('state'):
                        node_data['state'] = {'expanded': True}
                        break
            yield node_data
    return [g for g in inner(node_set)]


def get_nodes_2(request):
    permission_list = [per for per in request.session.get('permission_list') if per.get('type') != 'button']
    permission_dict = {}

    # 把全部菜单权限的记录存放到字典permission_dict
    for per in permission_list:
        temp_dict = {}
        temp_dict['text'] = per.get('title')
        temp_dict['href'] = per.get('url') or ''
        temp_dict['pid'] = per.get('pid')
        # temp_dict['nodes'] = []

        permission_dict[per.get('id')] = temp_dict

    # 构建树形结构的数据
    permission_tree_list =[]
    for per_id, per in permission_dict.items():
        pid = per.get('pid')
        if pid:
            if not permission_dict[pid].get('nodes'):
                permission_dict[pid]['nodes'] = []
            permission_dict[pid]['nodes'].append(per)
        else:
            permission_tree_list.append(per)

        if request.path == per['href']:
            while pid:
                permission_dict[pid]['state'] = {'expanded': True}
                pid = permission_dict[pid]['pid']
    return permission_tree_list

# @register.inclusion_tag('rbac/nav_path.html')
# def get_tree_list(request):
#     pres = get_nodes_2(request)
#     def foo(lis:list):
#         for pre in pres:
#             if pre.get('state'):
#                 yield pre['text']
#                 foo(pre['nodes'])
#             else:
#                 print('========================', pre)
#                 print(pre['href'],'=======', request.path)
#                 if pre['href'] == request.path:
#                     print(pre['text'])
#                     yield pre['text']
#
#     pres_tree_path = [g for g in foo(pres)]
#     pprint.pprint(pres_tree_path)
#     return {'pres_tree_path': pres_tree_path}

@register.inclusion_tag('rbac/nav_path.html')
def get_tree_list(request):
    permission_list = [per for per in request.session.get('permission_list') if per.get('type') == 'menu']
    path_tree_list = []

    # 把全部菜单权限的记录存放到字典permission_dict
    permission_dict = {}
    for per in permission_list:
        temp_dict = {}
        temp_dict['text'] = per.get('title')
        temp_dict['href'] = per.get('url') or ''
        temp_dict['pid'] = per.get('pid')
        # temp_dict['nodes'] = []

        permission_dict[per.get('id')] = temp_dict
    #
    temp = None
    for per_id, per in permission_dict.items():
        if per['href'] == request.path:
            temp = per
            while temp:
                path_tree_list.append(temp['text'])
                if not temp['pid']:break
                temp = permission_dict[temp['pid']]
    path_tree_list.reverse()

    return {'path_tree_list': path_tree_list}





@register.inclusion_tag('rbac/get_menu.html')
def get_menu(request):
    # default_data = get_nodes(permission_list, root_data)
    # permission_tree_list = get_nodes_g(permission_list, request.path)
    permission_tree_list = get_nodes_2(request)
    return {'permission_tree_list': json.dumps(permission_tree_list)}


# @register.inclusion_tag('rbac/get_menu.html')
@register.filter
def get_per_list(request):
    return request.user.is_superuser or request.path + 'add/' in [per['url'] for per in request.session['permission_list']]


# 030619101783
# zpzhue0903


@register.filter
def hander_per(show_list, request):
    heads = show_list.get_heads()
    body = show_list.get_body()

    btn_per = [per['url'] for per in request.session['permission_list'] if per['type']=='button']
    for row in body:
        for per in btn_per:
            c = re.compile(per)
            if not re.search(c, '--'.join(row)):
                body.remove(per)

    return heads