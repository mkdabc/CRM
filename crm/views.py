from django.shortcuts import render,HttpResponse,redirect

# Create your views here.
from .models import *


class Per(object):
    def __init__(self,actions):
        self.actions=actions
    def add(self):
        return "add" in self.actions
    def delete(self):
        return "delete" in self.actions
    def edit(self):
        return "edit" in self.actions
    def list(self):
        return "list" in self.actions




def users(request):

    user_list=User.objects.all()

    # permission_list=request.session.get("permission_list")
    #print(permission_list)

    # 查询当前登录人得名字

    id=request.session.get("user_id")
    user=User.objects.filter(id=id).first()

    per=Per(request.actions)

    return render(request, "rbac/users.html", locals())


import re
def add_user(request):


    return HttpResponse("add user.....")

def del_user(request,id):
    return HttpResponse("del"+id)

def edit_user(request,id):
    return HttpResponse("edit"+id)

def roles(request):
    # 查询当前登录人得名字
    id = request.session.get("user_id")
    user = User.objects.filter(id=id).first()
    role_list=Role.objects.all()
    per = Per(request.actions)
    return render(request, "rbac/roles.html", locals())


from rbac.service.perssions import *

def login(request):
    if  request.method=="POST":
        user=request.POST.get("user")
        pwd=request.POST.get("pwd")
        user=User.objects.filter(userinfo__username=user,userinfo__password=pwd).first()
        if user:
            ############################### 在session中注册用户ID######################
            request.session["user_id"]=user.pk
            ###############################在session注册权限列表##############################
            # 查询当前登录用户的所有角色
            # ret=user.roles.all()
            # print(ret)# <QuerySet [<Role: 保洁>, <Role: 销售>]>

            # 查询当前登录用户的所有权限，注册到session中
            initial_session(user,request)

            #return HttpResponse("登录成功！")
            return redirect("/stark/crm/customer/")
    return render(request,"login.html")

