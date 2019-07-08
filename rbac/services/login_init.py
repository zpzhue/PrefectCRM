

def permission_init(request, obj):
    permission_list = []
    permissions = obj.role.all().values('permission__id',
                                        'permission__url',
                                        'permission__title',
                                        'permission__type',
                                        'permission__parent_id',
                                        ).distinct()
    for per in permissions:
        permission_list.append({
            'id': per.get('permission__id'),
            'url': per.get('permission__url') or '',
            'title': per.get('permission__title'),
            'type': per.get('permission__type'),
            'pid': per.get('permission__parent_id') or ''
        })

    request.session['permission_list'] = permission_list
