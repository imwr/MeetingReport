from django.contrib import admin
from MeetingReports.models import UserGroup, UserProfile, Emails, Reports, Company, Meeting
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class GroupAdminNew(admin.ModelAdmin):
    list_display = ('name', 'get_author', 'master_display', 'created_time', 'last_modified_time')

    def get_author(self, obj):
        return obj.ower.username

    def master_display(self, obj):
        return ", ".join([p.username for p in obj.master.all()])

    def has_add_permission(self, request):
        if request.user.is_superuser or request.user.is_staff:
            return True
        # 每个用户只允许添加一个组
        usergroup = UserGroup.objects.get(ower_id=request.user.id)
        if usergroup:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.user.is_superuser:
            return super(GroupAdminNew, self).change_view(request, object_id, extra_context=extra_context)
        # 当前用户不是小组管理员
        usergroup = UserGroup.objects.get(pk=object_id)
        if request.user.id != usergroup.ower.id:
            extra_context = extra_context or {}
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False

        return super(GroupAdminNew, self).change_view(request, object_id, extra_context=extra_context)


# Define an inline admin descriptor for UserProfile model
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


# Define a new User admin
class UserAdminNew(UserAdmin):
    inlines = (UserProfileInline,)


# Define a new User admin
class UserProfileAdminNew(admin.ModelAdmin):
    model = UserProfile

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            UserProfile.objects.get(pk=request.user.id)
        except UserProfile.DoesNotExist:
            return True
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.user.is_superuser:
            return super(UserProfileAdminNew, self).change_view(request, object_id, extra_context=extra_context)
        user = User.objects.get(pk=object_id)
        if request.user.id != user.id:
            extra_context = extra_context or {}
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False

        return super(UserProfileAdminNew, self).change_view(request, object_id, extra_context=extra_context)


class EmailsAdmin(admin.ModelAdmin):
    list_display = ('group', 'contain_menber', 'relist_display', 'cclist_display')
    search_fields = ('group',)
    can_delete = False

    def relist_display(self, obj):
        return ", ".join([p.username for p in obj.relist.all()])

    def cclist_display(self, obj):
        return ", ".join([p.username for p in obj.cclist.all()])

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        # 每个组只允许添加一个邮件组
        userprofile = UserProfile.objects.get(user_id=request.user.id)
        emails = Emails.objects.get(group_id=userprofile.group_id)
        if emails:
            return False
        return True

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if request.user.is_superuser:
            return super(EmailsAdmin, self).change_view(request, object_id, extra_context=extra_context)
        # 当前用户不是小组管理员
        emails = Emails.objects.get(pk=object_id)
        usergroup = UserGroup.objects.get(pk=emails.group_id)
        if request.user.id != usergroup.ower.id:
            extra_context = extra_context or {}
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False

        return super(EmailsAdmin, self).change_view(request, object_id, extra_context=extra_context)


class ReportsAdmin(admin.ModelAdmin):
    list_display = ('user', 'meeting', 'last_modified_time')
    search_fields = ('created_time',)
    can_delete = False


class MeetingAdmin(admin.ModelAdmin):
    list_display = ('topic', 'noter', 'milestone1', 'last_modified_time')
    search_fields = ('created_time',)
    can_delete = False


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'mobile', 'address')
    can_delete = False


admin.site.register(UserGroup, GroupAdminNew)
admin.site.register(Emails, EmailsAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Reports, ReportsAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(UserProfile, UserProfileAdminNew)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdminNew)
