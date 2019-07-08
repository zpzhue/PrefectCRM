import copy


from django.urls import path, re_path, reverse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist
from django import forms
from stark.utils.pages import Paginator
from django.db.models import Q
from django.db.models.fields.related import ForeignKey,ManyToManyField

class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if isinstance(field, forms.DateField):
                # self.fields[name] = forms.DateField(
                #     widget=forms.PasswordInput(attrs={'class': 'input is-hovered form-control', 'type': 'date'}))
                field.widget.input_type = 'date'
                field.widget.format = '%Y-%m-%d'


class ShowList:

    def __init__(self, modelstrak, queryset, request):
        self.modelstrak = modelstrak
        self.queryset = queryset
        self.request = request
        self.search_result = self.get_query_result()

    def get_search_condition(self):
        val = self.request.GET.get('q')
        search_condition = Q()
        if val:
            self.search_default_val = val
            search_condition.connector = 'or'
            for search_field in self.modelstrak.search_list:
                search_condition.children.append((search_field + '__icontains', val))
        return search_condition

    def get_filter_condition(self):
        filter_condition = Q()
        for k, v in self.request.GET.items():
            if k in ['page', 'q']:
                continue
            filter_condition.children.append((k, v))
        return filter_condition

    def page_data(self):
        current_page = self.request.GET.get('page')
        self.paginator = Paginator(current_page, self.request, self.search_result.count(), 8, 7)
        return self.search_result[self.paginator.start : self.paginator.end]

    # 获取表头列表

    def get_query_result(self):
        return self.queryset.filter(self.get_search_condition()).filter(self.get_filter_condition())

    def get_heads(self):
        head_list = []
        for field in self.modelstrak.get_head_list_display():
            try:
                field_obj = self.modelstrak.model._meta.get_field(field)  # 如果
                head_list.append(field_obj.verbose_name)
            except FieldDoesNotExist as e:
                if field == '__str__':
                    val = self.modelstrak.model._meta.model_name.upper()
                else:
                    val = field(self.modelstrak, is_get_header=True)
                head_list.append(val)
        return head_list

    # 获取表格数据（包括自定义数据）
    def get_body(self):
        data = []  # 用户保存数据的，最终结格式为:  [[td, td, td...], [td, td, '''], [...]]
        for obj in self.page_data():
            temp = []
            for field in self.modelstrak.get_head_list_display():   # 循环要显示的字段列表
                # val = field(self, obj) if callable(field) else getattr(obj, field)
                if callable(field):                                 # 判断是否可调用，如果可调用，则是自定义的字段
                    val = field(self.modelstrak, obj)                          # 执行自定义的函数，把obj对象传入，获取对应的field
                else:
                    try:
                        if self.modelstrak.model._meta.get_field(field).choices:    # 判断field是否存在choices属性，如果存在，特殊处理，展示choice字段
                            val = getattr(obj, f'get_{field}_display')()            # obj代表当前字段对象，使用  get_xxx_display() 方法获取choices展示字段
                        else:
                            val = getattr(obj, field) or ''               # 如果不可调用则是模型类的字段，使用反射的方式获取对应字段的值
                    except FieldDoesNotExist as e:                  # 处理list_display列表中为默认字段，即__str__是处理方法
                        val = getattr(obj, field)()                 # 执行obj.__str__() 方法
                if field in self.modelstrak.list_display_link:
                    val = f'<a href="{obj.pk}/change/">{val}</a>'   # 生成编辑的链接标签
                temp.append(mark_safe(val))                         # 把每一列数据添加到临时列表

            data.append(temp)  # 把每一行数据添加到数据类表中

        return data

    def show_actions(self):
        actions = []

        for action in self.modelstrak.get_actions():
            actions.append({
                'name': action.__name__,
                'desc': action.short_desc or action.__name__
            })
        return actions

    def show_list_filter(self):
        list_filte = {}         # 最终数据 {'publish':[link1, link2, link3], 'authors':[link1, link2, link3]}

        # 获取要过滤字段的数据：如果是模型类就取所有的行记录，如果choice字段就显示get_xxx_display() ，普通字段默认不显示
        for field in self.modelstrak.list_filter:                               # 遍历取出list_filter中定义的自端倪 ['publish', 'author']
            params = copy.deepcopy(self.request.GET)                            # 先复制上次搜索请求的参数，做保留搜索条件用
            field_obj = self.modelstrak.model._meta.get_field(field)            # 获取list_filter中
            if isinstance(field_obj, (ForeignKey, ManyToManyField)):            # 处理一对多字段和多对多字段
                relate_model = field_obj.remote_field.model
                data_set = relate_model.objects.all()
            elif field_obj.choices:                                             # 处理有choices属性的字段
                data_set = field_obj.choices
            else:data_set = []                                                  # 处理普通字段（这里默认不处理）

            # 处理params 参数,没有查询把查询参数去掉，页码从1开始
            if params.get('q') == '':
                params.pop('q')
            params['page'] ='1'

            # 渲染生成筛选条件的a标签
            links = []
            if params.get(field):       # 处理all 过滤标签
                del params[field]
                links.append(f'<a href="?{params.urlencode()}" class="btn btn-sm btn-default">全部</a>')
            else:
                links.append(f'<a href="?{params.urlencode()}" class="btn btn-sm btn-primary">全部</a>')      # 没有过滤条件，默认加上btn-primary 样式

            for data in data_set:
                current_filed_id = self.request.GET.get(field)
                pk, text = data if isinstance(data, tuple) else (data.pk, str(data))

                params[field] = str(pk)
                if current_filed_id == str(pk):                                                                      # 渲染当选选中过滤条件的标签颜色变深btn-primary
                    links.append(f'<a href="?{ params.urlencode() }" class="btn btn-sm btn-primary">{ text }</a>')
                else:
                    links.append(f'<a href="?{ params.urlencode() }" class="btn btn-sm btn-default">{ text }</a>')

            list_filte[field_obj.verbose_name] = links
        return list_filte


class ModelStrak:
    # 定义显示的列
    list_display = ['__str__']
    list_display_link = []
    search_list = []
    model_form_class = None

    actions = []
    list_filter = []

    # 初始化函数，传入model并保存为实例变量
    def __init__(self, model):
        self.model = model
        self.model_name = model._meta.model_name
        self.model_name_display = model._meta.verbose_name
        self.app_name = model._meta.app_label

        self.list_view_url_alais = f'{self.app_name}_{self.model_name}'
        # self.list_view_url = reverse(f'{self.app_name}_{self.model_name}')

    def get_model_form_class(self):
        class DetailModelForm(BaseModelForm):
            class Meta:
                model = self.model
                fields = '__all__'

        return self.model_form_class or DetailModelForm

    # 更新要显示的列，包括一些默认的列，如checkbox和编辑删除按钮等
    def get_head_list_display(self):
        oprertion = [ModelStrak._delete] if self.list_display_link else [ModelStrak._edit, ModelStrak._delete]
        return [ModelStrak.checkbox] + self.list_display + oprertion

    # 自定义checkbox，和标题
    def checkbox(self, obj=None, is_get_header=False):
        if is_get_header:
            return mark_safe("<input type='checkbox' class='select_all_ckb' name='all_checked' />")
        return mark_safe(f"<input type='checkbox' class='select_ckb' name='choice_pk' value='{ obj.pk }'/>")

    # 编辑按钮
    def _edit(self, obj=None, is_get_header=False):
        if is_get_header:
            return '编辑'
        # return mark_safe(f"<a href='{obj.pk}/change/'>编辑</a>")
        return mark_safe(f"<a href='/stark/{self.app_name}/{self.model_name}/{obj.pk}/change/'>编辑</a>")

    # 删除按钮
    def _delete(self, obj=None, is_get_header=False):
        if is_get_header:
            return '删除'
        # return mark_safe(f"<a href='{obj.pk}/delete/'>删除</a>")
        return mark_safe(f"<a href='/stark/{self.app_name}/{self.model_name}/{obj.pk}/delete/'>删除</a>")

    def patch_delete(self,request,  queryset):
        queryset.delete()
    patch_delete.short_desc = '批量删除'

    def get_actions(self):
        return [self.patch_delete] + self.actions

    def list_view(self, request, data=None):
        '''
        默认查看的视图
        :param request:
        :return:
        '''

        # 实例化展示类
        if request.method == 'POST':
            '''
            actions处理部分
            '''

            patch_action = request.POST.get('patch_action')             # 获取要执行的actions函数
            choice_pk = request.POST.getlist('choice_pk')               # 获取要操作（选择的）queryset主键
            queryset = self.model.objects.filter(pk__in=choice_pk)      # 过滤queryset by pk
            ret = getattr(self, patch_action, queryset)(request, queryset)
            if ret:                                                     # 如果有返回值就返回自定义内容，如果没有执行下面GET处理流程
                return ret

        if data:
            queryset = data.get('queryset')
            self.actions = data.get('actions')
            self.list_filter = data.get('list_filter')
        else:
            queryset = self.model.objects.all()
            self.actions = self.__class__.__dict__.get('actions', [])
            self.list_filter = self.__class__.__dict__.get('list_filter', [])


        show_list = ShowList(self, queryset, request)

        # heads = show_list.get_head_list()
        # data = show_list.get_data_list(queryset[page.start: page.end])
        return render(request, 'stark/list_view.html', {'list_display': self.list_display,
                                                        'model_name': self.model_name_display,
                                                        'show_list': show_list})

    def add_view(self, request):
        '''
        添加数据视图
        :param request:
        :return: HttpRespones
        '''

        CurrentModelForm = self.get_model_form_class()

        if request.method == 'GET':
            form = CurrentModelForm()
            return render(request, 'stark/add_view.html', {'form': form,
                                                           'method': '添加',
                                                           'model_name': self.model_name_display,
                                                           'index_url': self.list_view_url_alais})

        form = CurrentModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse(self.list_view_url_alais))
        else:
            return render(request, 'stark/add_view.html', {'form': form,
                                                           'method': '添加',
                                                           'model_name': self.model_name_display,
                                                           'index_url': self.list_view_url_alais})

    def change_view(self, request, id):
        '''
        修改数据视图
        :param request:
        :param id:
        :return:
        '''

        CurrentModelForm = self.get_model_form_class()
        obj = self.model.objects.filter(pk=id).first()

        if request.method == 'GET':
            form = CurrentModelForm(instance=obj)
            return render(request, 'stark/add_view.html', {'form': form,
                                                           'method': '保存',
                                                           'model_name': self.model_name_display,
                                                           'index_url': self.list_view_url_alais})

        form = CurrentModelForm(request.POST, instance=obj)

        if form.is_valid():
            form.save()
            return redirect(reverse(self.list_view_url_alais))
        else:
            return render(request, 'stark/change.html', {'form': form,
                                                         'method': '保存',
                                                         'model_name': self.model_name_display,
                                                         'index_url': self.list_view_url_alais})

    def delete_view(self, request, id):
        '''
        删除数据视图
        :param request:
        :param id:
        :return:
        '''
        obj = self.model.objects.filter(pk=id).first()
        if request.method == 'GET':
            return render(request, 'stark/delete_view.html', {'obj': obj,
                                                              'model_name': self.model_name_display,
                                                              'index_url': self.list_view_url_alais
                                                              })
        obj.delete()
        return redirect(reverse(self.list_view_url_alais))

    def extra_url(self):
        '需要扩展url时，在自己编写的ModelStark里面重写这个方法'
        return []

    @property
    def urls(self):
        '''
        二级url分发
        :return:
        '''
        urlpatterns = [
                   path('', self.list_view, name=self.list_view_url_alais),
                   path('add/', self.add_view),
                   re_path('(\d+)/change/', self.change_view),
                   re_path('(\d+)/delete', self.delete_view),
        ]
        urlpatterns.extend(self.extra_url())

        return urlpatterns, None, None


class StarkSite:

    def __init__(self):
        '''
        初始化函数，self._registry字典用于保存模型类和模型配置类的对应关系
        '''
        self._registry = {}

    def register(self, model, Stark_class=None):
        '''
        模型配置类的 注册函数 ==》  {model：Stark_class(model)}
        :param model:
        :param Stark_class:
        :return:
        '''
        Stark_class = Stark_class or ModelStrak
        self._registry[model] = Stark_class(model)

    def get_urls(self):
        '''
        一级url分发
        :return:
        '''
        temp_urls = []
        for model, model_config in self._registry.items():
            model_name, app_label = model._meta.model_name, model._meta.app_label
            temp_urls.append(
                path(f'{app_label}/{model_name}/', model_config.urls),
            )
        return temp_urls

    @property
    def urls(self):
        return self.get_urls(), None, None


# 模块化方式的单例对象 site
site = StarkSite()
