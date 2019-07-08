from django.urls import path
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from stark.service.sites import site, ModelStrak
from crm import models

class UserStark(ModelStrak):
    list_display = ['name', ]


class CustomerStark(ModelStrak):

    def status(self, obj=None, is_get_header=False):
        if is_get_header:
            return '跟进状态'
        status_color = {
            "studying": "#71C671",
            "signed": "#1C86EE",
            "unregistered": "#EE3B3B",
            "paid_in_full": "#9F79EE"
        }
        return mark_safe(
            "<span style='background-color:%s;color:white;padding:4px;display:inline-block;width:90px'>%s</span>" % (
            status_color[obj.status], obj.get_status_display()))

    def class_list(self, obj=None, is_get_header=False):
        if is_get_header:
            return '所报班级'

        td = [f'{clazz.get_course_display()}{clazz.semester}({clazz.campuses})' for clazz in obj.class_list.all() ]

        return mark_safe('</br>'.join(td))

    def own2public(self, request, queryset):
        queryset.update(consultant=None)
    own2public.short_desc = '私海客户转公海客户'

    def public2own(self, request, queryset):
        queryset.update(consultant=request.user.pk)
    public2own.short_desc = '公海客户转私海客户'

    def own_customer(self, request):
        data = {
            'queryset': models.Customer.objects.filter(consultant=request.user.pk),
            'actions': [CustomerStark.own2public],
            "list_filter": ["status", "class_list"],
        }
        return self.list_view(request, data)

    def publick_customer(self, request):
        data = {
            'queryset': models.Customer.objects.filter(consultant=None),
            'actions': [CustomerStark.public2own],
            "list_filter": ["status", "class_list"],
        }
        return self.list_view(request, data)

    def extra_url(self):
        urlpatterns = [
            path('own_customer/', self.own_customer),
            path('publick_customer', self.publick_customer),
        ]

        return urlpatterns

    list_display = ['name', 'qq', 'qq_name', 'source', 'consultant', class_list, status]
    list_filter = ['status', 'consultant', ]
    search_list = ['qq', 'name']


class ConsultRecordAdmin(ModelStrak):



    list_display = ['consultant', 'customer', 'note', 'status', 'date']


site.register(models.User)
site.register(models.Customer, CustomerStark)
site.register(models.Department)
site.register(models.Campuses)
site.register(models.Klass)
site.register(models.ConsultRecord, ConsultRecordAdmin)