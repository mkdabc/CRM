import copy

class PageInfo:
    def __init__(self, page_num, all_data,param, per_page, base_page):
        '''
        :param page_num: 当前页
        :param per_page: 每页数据数量
        :param all_data: 总数据量
        :param base_page: 固定页数
       '''
        try:
            self.page_num = int(page_num)
        except Exception as e:
            self.page_num = 1
        self.per_page = int(per_page)
        self.all_data = all_data
        self.base_page = int(base_page)
        self.param = copy.deepcopy(param)

    def start(self):
        return (self.page_num - 1) * self.per_page

    def end(self):
        return self.page_num * self.per_page

    # 总页数函数（总数据/每页条数）
    def total_pages(self):
        a, b = divmod(self.all_data, self.per_page)
        if b:
            a = a + 1
        return a

    def pager(self):
        page_list = []
        harf = divmod(self.base_page, 2)[0]
        # 如果总页数小于固定分页
        if self.total_pages() <= self.base_page:
            begin = 1
            end = self.total_pages()
        # 如果当前页 + 固定页的一半大于总页数
        elif self.page_num + harf >= self.total_pages():
            begin = self.total_pages() - self.base_page + 1
            end = self.total_pages()
    # 如果当前页小于harf+1
        elif self.page_num < harf + 1:
            begin = 1
            end = self.base_page
        else:
            begin = self.page_num - harf
            end = self.page_num + harf

        #首页
        first_page = '<li><a href="?p=1">首页</a></li>'
        page_list.append(first_page)
        # 上一页
        if self.page_num <= 1:
            prev = '<li><a href="#">上一页</a></li>'
        else:
            self.param['p'] = self.page_num - 1
            prev = '<li><a href="?%s">上一页</a></li>' % (self.param.urlencode())
        page_list.append(prev)

        for i in range(begin, end + 1):
            self.param["p"] = i
            if i == self.page_num:
                temp = '<li class="active"><a href="?%s">%s</a></li>' % (self.param.urlencode(), i)
            else:
                temp = '<li><a href="?%s">%s</a></li>' % (self.param.urlencode(), i)
            page_list.append(temp)

        # 下一页
        if self.page_num >= self.total_pages():
            prev = '<li><a href="#">下一页</a></li>'
        else:
            self.param['p'] = self.page_num + 1
            prev = '<li><a href="?%s">下一页</a></li>' % (self.param.urlencode())
        page_list.append(prev)

        #尾页
        end_page = '<li><a href="?p=%s">尾页</a></li>'%(self.total_pages())
        page_list.append(end_page)
        # print(page_list)
        return page_list

