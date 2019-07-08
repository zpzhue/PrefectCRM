import copy


class Paginator(object):
    def __init__(self, current_page, request, total_data_count, pre_page_data_count, max_page_num):
        """
        封装分页相关数据
        :param current_page:          当前页
        :param total_data_count:      数据库中的数据总条数
        :param pre_page_data_count:   每页显示的数据条数
        :param max_pager_num:         最多显示的页码个数
        :param num_pages:             计算总页数
        """

        # 获取当前页数
        try:
            self.current_page = int(current_page)
            if self.current_page < 1:
                raise ValueError()
        except Exception as e:
                self.current_page = 1

        # request.GET
        self.params = copy.deepcopy(request.GET)

        # 总数据量， 数据库里面存放的总数据数量
        self.total_data_count = total_data_count

        # 每页显示的数据的数量
        self.pre_page_data_count = pre_page_data_count

        # 每页显示的最大页码个数
        self.max_page_num = max_page_num
        self.page_num_half = int(max_page_num / 2)

        # 计算总页数 值
        total_page_num, rem = divmod(total_data_count, pre_page_data_count)
        self.tatol_page_num = total_page_num if not rem else total_page_num + 1

    @property
    def start(self):
        '''
        获取起始数据值的索引
        :return:
        '''
        return (self.current_page - 1) * self.pre_page_data_count

    @property
    def end(self):
        '''
        获取结束数据值的索引
        :return:
        '''
        return self.current_page * self.pre_page_data_count


    def page_html(self):
        '''
        获取页码的html代码
        :return:
        '''
        start_page, end_page = 0, 0
        # 当数据的总页数 小于 最大可以展示的页码数
        if self.tatol_page_num < self.max_page_num:
            start_page = 1
            end_page = self.tatol_page_num + 1
        # 数据总页数 大于 最大页码数
        else:
            if self.current_page <= self.page_num_half:
                start_page = 1
                end_page = self.max_page_num + 1
            elif (self.current_page + self.page_num_half) > self.tatol_page_num:
                start_page = self.tatol_page_num - self.max_page_num + 1
                end_page = self.tatol_page_num + 1
            else:
                start_page = self.current_page - self.page_num_half
                end_page = self.current_page + self.page_num_half + 1


        page_html_list = ['<nav aria-label="Page navigation" class="text-center"><ul class="pagination">']

        # 添加首页标签
        self.params['page'] = "1"

        page_html_list.append(f'<li><a href="?{ self.params.urlencode() }" aria-label="Previous"><span aria-hidden="true">首页</span></a></li>')

        #添加上一页标签
        if self.current_page <=1:
            pre_page = '<li class="disabled"><a href="javascript:void(0);" aria-label="Previous"><span aria-hidden="true">上一页</span></a></li>'
        else:
            self.params['page'] = str(self.current_page - 1)
            pre_page = f'<li><a href="?{ self.params.urlencode() }" aria-label="Previous"><span aria-hidden="true">上一页</span></a></li>'
        page_html_list.append(pre_page)

        # 添加页码标签
        for i in range(start_page, end_page):
            self.params['page'] = str(i)
            if self.current_page == i:
                tag_a = f'<li class="active"><a href="?{ self.params.urlencode() }">{i}</a></li>'
            else:
                tag_a = f'<li><a href="?{ self.params.urlencode() }">{i}</a></li>'
            page_html_list.append(tag_a)

        # t添加下一页标签
        if self.current_page >= self.tatol_page_num:
            next_page = '<li class="disabled"><a href="javascript:void(0);" aria-label="Previous"><span aria-hidden="true">下一页</span></a></li>'
        else:
            self.params['page'] = str(self.current_page + 1)
            next_page = f'<li><a href="?{ self.params.urlencode() }" aria-label="Previous"><span aria-hidden="true">下一页</span></a></li>'
        page_html_list.append(next_page)

        # 添加尾页标签
        self.params['page'] = str(self.tatol_page_num)
        page_html_list.append(f'<li><a href="?{ self.params.urlencode() }" aria-label="Previous"><span aria-hidden="true">尾页</span></a></li>')

        page_html_list.append('</ul></nav>')

        return ''.join(page_html_list)