from stark.service.sites import *
from rbac.models import *



class PermissionConfig(ModelXadmin):
    list_display = ['id','title','url','group','action']
site.register(User)
site.register(Role)
site.register(Permission,PermissionConfig)
site.register(PermissionGroup)