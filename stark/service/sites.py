# 注册信息
from django.conf.urls import url
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models.fields.related import ForeignKey,ManyToManyField
from stark.service.pageinfo import *


class ShowList(object):
    def __init__(self, config_obj, data_list, request):
        self.request = request
        self.config_obj = config_obj  # self.config_obj == ModelXadmin实例化对象(self)
        self.data_list = data_list  # 包含所有对象的queryset
        # 分页
        self.page_num = request.GET.get('p')
        self.all_data = self.data_list.count()
        self.page = PageInfo(self.page_num, self.all_data, request.GET, 10, 11)
        self.per_page_msg = self.data_list[self.page.start():self.page.end()]
        # print(self.per_page_msg)

    # 构建表头部分
    def get_header(self):
        header_list = []
        for field in self.config_obj.new_list_display():
            if isinstance(field, str):
                if field == '__str__':
                    val = self.config_obj.model._meta.model_name
                else:
                    field_obj = self.config_obj.model._meta.get_field(field)
                    val = field_obj.verbose_name
            else:
                val = field(self.config_obj,header=True)
            header_list.append(val)
        return header_list

    # 构建数据表单部分
    def get_body(self, querset_obj=None):
        new_data_list = []  # 新建一个空字典
        # for obj in self.data_list:  # 取到所有的对象 ['python','linux']
        if not querset_obj:
            # 不筛选的时候默认为当前页的总数据
            querset = querset_obj
        else:
            # 传入筛选过的queryset时，循环该对象
            querset = self.per_page_msg
        # print(querset)
        for obj in querset:
            temp = []
            for field in self.config_obj.new_list_display():  # ['price','title'] 用户自定义的list_display值,默认为__str__方法
                from django.db.models.fields.related import ManyToManyField
                if isinstance(field, str):
                    if field in ['check', '__str__', 'edit', 'delete']:
                        val = getattr(obj, field)
                    else:  # 如果为多对多字段的话
                        field_obj = self.config_obj.model._meta.get_field(field)
                        if isinstance(field_obj, ManyToManyField):  # 判断field_obj字段是否属于多对多字段
                            many_data_list = getattr(obj, field).all()  # 如果是多对多字段，book.author.all()取到所有作者对象
                            item = [str(item) for item in many_data_list]
                            val = ','.join(item)
                        else:  # 非多对多字段
                            if field_obj.choices:
                                val = getattr(obj,'get_'+field+'_display')
                            else:
                                val = getattr(obj, field)
                            if field in self.config_obj.list_display_links:
                                _url = '{}{}/{}'.format(self.request.path, obj.pk, 'change')
                                val = mark_safe('<a href="%s">%s</a>' % (_url, val))
                else:  # 如果是函数形式的话
                    val = field(self.config_obj, obj)
                temp.append(val)
            new_data_list.append(temp)
        return new_data_list

    # 搜索函数
    def get_search(self,request):
        ret = copy.deepcopy(self.request.GET)
        val = ret.get('search', '')
        # self.val = val
        search_condition = Q()
        if val:
            search_condition.connector = 'or'
            for field in self.config_obj.search_fields:
                search_condition.children.append((field + '__icontains', val))
            # ret = self.config_obj.model.objects.filter(search_condition).distinct()
        return search_condition  # 返回一个筛选完的queryset对象

    # actions
    def get_new_actions(self):
        temp = []
        temp.extend(self.config_obj.actions)
        temp.append(self.config_obj.patch_delete)
        new_actions = []
        for func in temp:
            dic = {
                'text': func.short_description,
                'name': func.__name__,
            }
            new_actions.append(dic)
        # print(new_actions)
        return new_actions

    # filter
    def get_filter(self):
        filter_list = {}
        if self.config_obj.list_filter:
            for field in self.config_obj.list_filter:  # ['title', 'publish', 'authors']
                get_id = self.request.GET.get(field, 0)
                # print('get_id',get_id)
                params = copy.deepcopy(self.request.GET)  #获取get请求值
                field_obj = self.config_obj.model._meta.get_field(field) #获取该表的字段对象
                rel_model = field_obj.rel
                temp = []
                # 处理ALL标签
                if params.get(field):
                    del params[field]
                    all_link = mark_safe('<td><a href="?%s">全部</a></td>') % (params.urlencode())
                    temp.append(all_link)
                else:
                    all_link = mark_safe('<td class="success"><a href="#">全部</a></td>')
                    temp.append(all_link)
                #处理一对多或者多对多标签
                if rel_model:
                    rel_queryset = rel_model.to.objects.all()  #取字段对象关联表QuerySet对象
                    # print('rel_queryset',rel_queryset)
                    for obj in rel_queryset:
                        params[field] = obj.pk   #以{field：obj.pk}形式放入params中
                        _urls = params.urlencode() #将params转换成URL形式
                        if int(get_id) == obj.pk:
                            links = mark_safe('<td class="success"><a href="?%s">%s</a></td>' % (_urls, str(obj)))
                        else:
                            links = mark_safe('<td><a href="?%s">%s</a></td>' % (_urls, str(obj)))
                        temp.append(links)
                #处理剩余标签
                else:
                    queryset = self.config_obj.model.objects.values(field, 'pk') #取得该表对象的field字段值和PK值
                    # print('queryset',queryset)
                    for i in queryset:
                        params[field] = i[field]
                        _urls = params.urlencode()
                        if get_id == i[field]:
                            links = mark_safe('<td class="success"><a href="?%s">%s</a></td>' % (_urls, i[field]))
                        else:
                            links = mark_safe('<td><a href="?%s">%s</a></td>' % (_urls, i[field]))
                        temp.append(links)
                filter_list[field] = temp
            # print('filter_list--------',filter_list)
            return filter_list


class ModelXadmin(object):
    list_display = ['__str__']
    search_fields = []
    modelform_class = []
    list_display_links = []
    actions = []
    list_filter = []

    def __init__(self, model):
        self.model = model  # 表对象Book,Publish,Author

    def edit(self, obj=None, header=False):
        if header:
            return '操作'
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse('%s_%s_change' % (app_label, model_name), args=(obj.pk,))
        return mark_safe("<a href='%s'>编辑</a>" % (_url))

    def delete(self, obj=None, header=False):
        if header:
            return '操作'
        return mark_safe("<a href='%s/delete/'>删除</a>" % (obj.pk))

    def check(self, obj=None, header=False):
        if header:
            return mark_safe('<input id="choice" type="checkbox">')
        return mark_safe("<input class='choice_item' type='checkbox' name='pk_list' value=%s>" % (obj.pk))

    def new_list_display(self):
        new_list = []
        new_list.append(ModelXadmin.check)
        new_list.extend(self.list_display)
        new_list.append(ModelXadmin.edit)
        new_list.append(ModelXadmin.delete)
        return new_list

    # action中使用patch_delete-->'删除数据'
    def patch_delete(self, request, queryset):
        queryset.delete()

    patch_delete.short_description = '删除数据'

    #构建filter的Q对象作为筛选项
    def get_filter_condition(self,request):
        filter_condition = Q()
        for filter_field,val in request.GET.items():
            # if filter_field in self.list_filter:
            if filter_field != 'p':
                field_obj = self.model._meta.get_field(filter_field)
                # print('field_obj',field_obj)
                if isinstance(field_obj,ManyToManyField) or isinstance(field_obj,ForeignKey):
                    filter_condition.children.append((filter_field+'__pk',val))
                else:
                    filter_condition.children.append((filter_field,val))
        # print('11111111',filter_condition)
        return filter_condition

    #显示界面
    def listview(self, request):
        # 收到POST请求数据后
        if request.method == 'POST':
            pk_list = request.POST.getlist('pk_list')
            queryset = self.model.objects.filter(pk__in=pk_list)
            action = request.POST.get('action')

            record = request.POST
            data ={}
            for key,val in request.POST.items():
                if key == 'csrfmiddlewaretoken'or key == 'action': continue
                field, pk = key.rsplit('_', 1)
                data[pk] = {field: val}
                # print(data)
            for pk, update_data in data.items():
                self.model.objects.filter(pk=pk).update(**update_data)
                # print(update_data)

            if action:
                action = getattr(self, action)  # 反射取到action函数
                action(request, queryset)  # 传参数调用
        data_list = self.model.objects.all()
        # 实例化一个ShowList对象
        show_list = ShowList(self, data_list, request)
        header_list = show_list.get_header()
        # 分页
        page_obj = show_list.page.pager()
        # actions
        actions = show_list.get_new_actions() # [{'text': '价格初始化', 'name': 'patch_init'}, {'text': '删除数据', 'name': 'patch_delete'}]传给前端
        # 搜索
        search_condition = show_list.get_search(request)  # 返回一个Q()
        # filter
        filter_list = show_list.get_filter()
        #展示filter后的数据
        filter_condition = self.get_filter_condition(request)  # 返回一个Q()

        data_list = self.model.objects.all().filter(search_condition).filter(filter_condition)
        body_list = show_list.get_body(data_list)
        return render(request, 'list_view.html', locals())

    # 自定义显示字段名默认为ModelForm默认显示
    def get_modelform_class(self):
        if not self.modelform_class:
            from django.forms import ModelForm
            class ModelFormDemo(ModelForm):
                class Meta:
                    model = self.model
                    fields = '__all__'
            # print('1111',ModelFormDemo)
            return ModelFormDemo
        else:
            return self.modelform_class

    def addview(self, request):
        # 调用实例对象的get_modelform_class()函数
        ModelFormDemo = self.get_modelform_class()
        # 实例化一个form对象
        form = ModelFormDemo()
        from django.forms.models import ModelChoiceField
        #判断bfield.field字段是否是ModelChoiceField类型，如果是则加一个标志bfield.is_pop = True
        for bfield in form:
            if isinstance(bfield.field,ModelChoiceField):
                bfield.is_pop = True
                bfield_model_name = bfield.field.queryset.model._meta.model_name
                bfield_app_label = bfield.field.queryset.model._meta.app_label
                # print(bfield_model_name)
                _url = reverse('%s_%s_add'%(bfield_app_label, bfield_model_name))
                bfield.url = _url + '?pop_res_id=id_%s'%(bfield.name)
                #将URL转换成 _url?pop_res_id=id_XXX形式

        if request.method == 'POST':
            form = ModelFormDemo(request.POST)
            if form.is_valid():
                obj = form.save()
                #获取select框的ID值
                pop_res_id = request.GET.get('pop_res_id')
                if pop_res_id:
                    res = {
                        'pk':obj.pk,
                        'text':str(obj),
                        'pop_res_id':pop_res_id
                    }
                    return render(request, 'pop.html', {'res':res})
                else:
                    return redirect(self.get_list_url())
        return render(request, 'addview.html', locals())

    def changeview(self, request, id):
        ModelFormDemo = self.get_modelform_class()
        edit_obj = self.model.objects.filter(pk=id).first()
        form = ModelFormDemo()
        if request.method == 'POST':
            form = ModelFormDemo(request.POST, instance=edit_obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            return render(request, 'changeview.html', locals())
        form = ModelFormDemo(instance=edit_obj)

        from django.forms.models import ModelChoiceField
        # 判断bfield.field字段是否是ModelChoiceField类型，如果是则加一个标志bfield.is_pop = True
        for bfield in form:
            # print(type(bfield.field))
            if isinstance(bfield.field, ModelChoiceField):
                bfield.is_pop = True
                bfield_model_name = bfield.field.queryset.model._meta.model_name
                bfield_app_label = bfield.field.queryset.model._meta.app_label
                _url = reverse('%s_%s_add' % (bfield_app_label, bfield_model_name))
                # print(_url)
                bfield.url = _url
                # print(bfield.url)

        return render(request, 'changeview.html', locals())

    def deleteview(self, request, id):
        if request.method == 'POST':
            self.model.objects.filter(pk=id).delete()
            return redirect(self.get_list_url())
        url = self.get_list_url()
        return render(request, 'delete.html', locals())


    def get_change_url(self,obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        # print("obj===========",obj)
        _url = reverse("%s_%s_change" % (app_label, model_name), args=(obj.pk,))
        return _url

    def get_delete_url(self, obj):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label

        _url = reverse("%s_%s_delete" % (app_label, model_name), args=(obj.pk,))
        return _url

    def get_add_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse("%s_%s_add" % (app_label, model_name))
        return _url

    def get_list_url(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        _url = reverse('%s_%s_list' % (app_label, model_name))
        return _url

    def extra_url(self):
        return []

    def get_urls(self):
        model_name = self.model._meta.model_name
        app_label = self.model._meta.app_label
        temp = [
            url(r'^$', self.listview, name='%s_%s_list' % (app_label, model_name)),
            url(r'add/$', self.addview, name='%s_%s_add' % (app_label, model_name)),
            url(r'(\d+)/change/$', self.changeview, name='%s_%s_change' % (app_label, model_name)),
            url(r'(\d+)/delete/$', self.deleteview, name='%s_%s_delete' % (app_label, model_name)),
        ]
        temp.extend(self.extra_url())
        return temp

    @property
    def urls(self):
        return (self.get_urls(), None, None)


class XadminSite(object):
    def __init__(self):
        self._registry = {}

    def register(self, model, admin_class=None):
        if not admin_class:
            admin_class = ModelXadmin
        self._registry[model] = admin_class(model)

    def get_urls(self):
        temp = []
        for model, config_obj in self._registry.items():
            model_name = model._meta.model_name  # 获取当前model的表名
            app_label = model._meta.app_label  # 获取所在的app名字
            temp.append(url(r'{}/{}/'.format(app_label, model_name), config_obj.urls))
        return temp

    @property
    def urls(self):
        return (self.get_urls(), None, None)


# 单例一个实例化对象
site = XadminSite()
