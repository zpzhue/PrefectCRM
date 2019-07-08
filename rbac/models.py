from django.db import models

# Create your models here.


class Permission(models.Model):
    title = models.CharField(max_length=32, verbose_name='权限')
    url = models.CharField(max_length=128, blank=True, null=True, verbose_name='访问url地址')
    type = models.CharField(max_length=32, choices=(('menu', '菜单权限'), ('link', '链接权限'), ('button', '按钮权限')),
                            default='button', verbose_name='资源类型')
    parent = models.ForeignKey(to='self', on_delete=models.CASCADE, verbose_name='父级权限',
                               default='', null=True,blank=True)

    def __str__(self):return self.title

    class Meta:
        verbose_name = '权限'


class Role(models.Model):
    name = models.CharField(max_length=32, verbose_name='角色类型')
    permission = models.ManyToManyField(to='Permission', verbose_name='权限')

    def __str__(self): return self.name

    class Meta:
        verbose_name = '角色'

class UserInfo(models.Model):
    # name = models.CharField(max_length=32, verbose_name='用户名')
    # passwd = models.CharField(max_length=32, verbose_name='密码')
    role = models.ManyToManyField(to=Role, verbose_name='角色')


    class Meta:
        abstract = True
        verbose_name = '用户'