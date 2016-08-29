from django.db import models
from django.contrib.auth.models import User
import json


# 小组
class UserGroup(models.Model):
    name = models.CharField('小组名', max_length=20, unique=True)
    ower = models.ForeignKey(User, blank=True)
    master = models.ManyToManyField(User, verbose_name='管理员', related_name='groupmaster', blank=True)
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modified_time = models.DateTimeField('修改时间', auto_now=True)

    def is_master(self, user):
        return user in self.master.split(",")

    def __str__(self):
        return self.name


# 公司信息
class Company(models.Model):
    name = models.CharField('名称', max_length=30, default='My Company', unique=True)
    name_ext = models.CharField('名称补充', max_length=30, default='better Co.,Ltd.')
    mission = models.CharField("使命", max_length=20, default='Try everything')
    url = models.URLField('多点商城', max_length=50, default='http://www.test.com')
    mobile = models.CharField('服务热线', max_length=11, default='11111111')
    address = models.CharField('公司地址', max_length=50, default='company address')

    def __str__(self):
        return self.name


# 用户
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    group = models.ForeignKey(UserGroup, verbose_name='小组', related_name='usergroup', blank=True, null=True)
    position = models.CharField('职位', max_length=20, default='SoftwareEngineer', blank=True)
    departments = models.CharField('部门', max_length=20, default='BusinessDepartment', blank=True)
    mobile = models.CharField('手机', max_length=11, unique=True, blank=True)
    duty = models.BooleanField('值日', default=False)
    sorts = models.PositiveIntegerField('排序', default=0, blank=True)
    company = models.ForeignKey(Company, verbose_name='公司')

    class Meta:
        ordering = ('sorts', 'user__date_joined',)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.duty:  # 值日True时，将其他成员置为Flase
            try:
                temp = UserProfile.objects.get(duty=True)
                if self != temp:
                    temp.duty = False
                    temp.save()
            except UserProfile.DoesNotExist:
                pass
        else:  # 值日False时，将下一成员置为True
            pass
        super(UserProfile, self).save(*args, **kwargs)


# 收件人列表
class Emails(models.Model):
    group = models.ForeignKey(UserGroup, verbose_name='小组')
    email = models.EmailField('组邮件', null=True)
    contain_menber = models.BooleanField('收件人是否包含全部组员（存在群邮箱时，此设置忽略）', default=True)
    relist = models.ManyToManyField(User, related_name='relist', verbose_name='附加收件人')
    cclist = models.ManyToManyField(User, related_name='cclist', verbose_name='抄送用户')

    def __str__(self):
        return self.group.name + '邮件表'


# 早会
class Meeting(models.Model):
    topic = models.CharField('主题', max_length=50, unique=True)
    noter = models.ForeignKey(User, related_name='noter', verbose_name='记录人')
    group = models.ForeignKey(UserGroup, verbose_name='所属小组')
    master = models.ForeignKey(User, related_name='master', verbose_name='主持人')
    menber = models.CharField('参会人员', max_length=100)
    position = models.CharField('会议地点', max_length=20, default='工位')
    milestone1 = models.CharField('里程碑', max_length=50)
    milestonedate1 = models.DateTimeField('里程碑时间')
    milestone2 = models.CharField('下一里程碑', max_length=50)
    milestonedate2 = models.DateTimeField('下一里程碑时间')
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modified_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.topic


# 早会内容
class Reports(models.Model):
    meeting = models.ForeignKey(Meeting, verbose_name='早会')
    user = models.ForeignKey(User, verbose_name='成员')
    leave = models.BooleanField('是否请假', default=False)
    content = models.CharField('早会条目', max_length=200)
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modified_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return str(self.user) + ", " + str(self.meeting)
