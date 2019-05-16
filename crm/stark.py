from stark.service.sites import site,ModelXadmin
from django.forms import ModelForm,widgets as wid
from .models import *
from django.db.models import Q
import datetime
from rbac.models import *
site.register(School)

class UserInfoModelForm(ModelForm):
    class Meta:
        model = UserInfo
        fields = '__all__'
        widgets = {
            'password':wid.PasswordInput(),
            'email':wid.EmailInput(),
        }

class UserConfig(ModelXadmin):
    def display_depart(self,obj=None,header=False):
        if header:
            return '部门'
        depart_id = obj.depart.pk
        return mark_safe('<a href="/stark/crm/department/%s/change/">%s</a>'%(depart_id,obj.depart))

    list_display = ["name","email",display_depart]
    modelform_class = UserInfoModelForm

site.register(UserInfo,UserConfig)


class ClassConfig(ModelXadmin):

    def display_classname(self,obj=None,header=False):
        if header:
            return "班级名称"
        class_name="%s(%s)"%(obj.course.name,str(obj.semester))
        return class_name

    list_display = [display_classname,"tutor","teachers"]

site.register(ClassList,ClassConfig)


from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import HttpResponse,redirect,render

class CusotmerConfig(ModelXadmin):

    def display_gender(self,obj=None,header=False):
        if header:
            return "性别"
        return obj.get_gender_display()

    def display_course(self,obj=None,header=False):
        if header:
            return "咨询课程"
        temp=[]
        for course in obj.course.all():
            s="<a href='/stark/crm/customer/cancel_course/%s/%s' style='border:1px solid #369;padding:3px 6px'><span>%s</span></a>&nbsp;"%(obj.pk,course.pk,course.name,)
            temp.append(s)
        return mark_safe("".join(temp))

    list_display = ["name",display_gender,display_course,"consultant",]

    def cancel_course(self,request,customer_id,course_id):
        # print(customer_id,course_id)
        obj=Customer.objects.filter(pk=customer_id).first()
        obj.course.remove(course_id)
        return redirect(self.get_list_url())

    def public_customer(self,request):
        user_id = 1  # request.session.get('user_id')
        now = datetime.datetime.now()
        dalta_day3 = datetime.timedelta(days=3)
        dalta_day15 = datetime.timedelta(days=15)
        customer_list = Customer.objects.filter(Q(last_consult_date__lt=now-dalta_day3)|Q(recv_date__lt=now-dalta_day15),status=2).exclude(consultant_id=user_id)
        # print(customer_list)
        return render(request, 'public_customer.html', locals())

    def further(self,request,customer_id):
        user_id = 2 #request.session.get('user_id')
        now = datetime.datetime.now()
        dalta_day3 = datetime.timedelta(days=3)
        dalta_day15 = datetime.timedelta(days=15)
        ret = Customer.objects.filter(pk=customer_id).filter(Q(last_consult_date__lt=now-dalta_day3)|Q(recv_date__lt=now-dalta_day15),status=2).update(consultant=user_id,last_consult_date=now,recv_date=now)
        if not ret:
            return HttpResponse('客户已经被跟进')
        CustomerDistrbute.objects.create(customer_id=customer_id,consultant_id=user_id,date=now,status=1)

        return HttpResponse('111')

    def my_customer(self,request):
        user_id = 2  #request.session.get('user_id')
        my_customer_list = CustomerDistrbute.objects.filter(consultant_id=user_id)

        return render(request, 'my_customer.html', locals())

    def extra_url(self):
        temp=[]
        temp.append(url(r"cancel_course/(\d+)/(\d+)",self.cancel_course))
        temp.append(url(r"public/",self.public_customer))
        temp.append(url(r"further/(\d+)",self.further))
        temp.append(url(r"my_customer",self.my_customer))
        return temp
site.register(Customer,CusotmerConfig)

site.register(Department)
site.register(Course)

class ConsultConfig(ModelXadmin):
    list_display = ['customer','consultant','date','note']
site.register(ConsultRecord,ConsultConfig)

class CourseRecordConfig(ModelXadmin):
    def course(self,request,course_record_id):
        if request.method == 'POST':
            data = {}
            for key,val in request.POST.items():
                if key == 'csrfmiddlewaretoken':continue
                field,pk = key.rsplit('_',1)
                if pk in data:
                    data[pk][field] = val
                else:
                    data[pk] = {field:val}
            # print(data)
            for pk,update_data in data.items():
                StudyRecord.objects.filter(pk=pk).update(**update_data)
            return redirect(self.get_list_url())

        study_record_list = StudyRecord.objects.filter(course_record=course_record_id)
        return render(request, 'score.html', locals())


    def extra_url(self):
        temp=[]
        temp.append(url(r"record_score/(\d+)/",self.course))
        return temp

    def record(self,obj=None,header=False):
        if header:
            return "考勤"
        return mark_safe('<a href="/stark/crm/studyrecord/?course_record=%s">记录</a>'%obj.pk)

    def record_score(self,obj=None,header=False):
        if header:
            return "录入成绩"
        return mark_safe('<a href="record_score/%s">录入成绩</a>'%(obj.pk))

    list_display = ['class_obj','day_num','teacher',record,record_score]

    def patch_studyrecord(self, request, queryset):
        temp = []
        for course_record in queryset:
            student_list = Student.objects.filter(class_list__id=course_record.class_obj.pk)
            for student in student_list:
                if not StudyRecord.objects.filter(student=student, course_record=course_record):
                    obj = StudyRecord(student=student, course_record=course_record)
                    temp.append(obj)
        StudyRecord.objects.bulk_create(temp)

    patch_studyrecord.short_description = '批量生产学习记录'
    actions = [patch_studyrecord]

site.register(CourseRecord,CourseRecordConfig)

class StudyConfig(ModelXadmin):
    def record(self,obj=None,header=False):
        if header:
            return '上课记录'
        tags = '<select name="record_%s" >'%(obj.pk)
        for record_choice in obj.record_choices:
            # print(obj.record)
            if record_choice[0] == obj.record:
                s_tag = mark_safe('<option selected value="%s">%s</option>' % (record_choice[0], record_choice[1]))
            else:
                s_tag = mark_safe('<option  value="%s">%s</option>'%(record_choice[0],record_choice[1]))
            tags += s_tag
        tags += '</select>'
        return mark_safe(tags)


    list_display = ['student','course_record',record,'score']
    # def patch_late(self,request,queryset):
    #     queryset.update(record='late')
    # patch_late.short_description = '迟到'
    # actions = [patch_late]
site.register(StudyRecord,StudyConfig)


from django.http import JsonResponse
class StudentConfig(ModelXadmin):
    def score_view(self,request,id):
        if request.is_ajax():
            sid = request.GET.get('sid')
            cid = request.GET.get('cid')
            study_record_list = StudyRecord.objects.filter(student=sid,course_record__class_obj=cid)
            data_list = []
            for study_record in study_record_list:
                day_num = study_record.course_record.day_num
                data_list.append(['day%s'%(day_num),study_record.score])
            # print(data_list)
            return JsonResponse(data_list,safe=False)

        else:
            student_obj = Student.objects.filter(pk=id).first()
            class_obj = ClassList.objects.filter(student__pk=id)

        return render(request, 'score_view.html', locals())

    def extra_url(self):
        temp=[]
        temp.append(url(r"score_view/(\d+)/",self.score_view))
        return temp


    def score_show(self,obj=None,header=False):
        if header:
            return '查看成绩'
        return mark_safe('<a href="score_view/%s">查看成绩</a>'%(obj.pk))

    list_display = ['customer','class_list',score_show]
    list_display_links = ['customer']
site.register(Student,StudentConfig)


site.register(CustomerDistrbute)