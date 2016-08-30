# -*- coding: utf-8 -*-

import json, datetime
from django.core.mail import EmailMultiAlternatives
from django.views.generic import View, DetailView, TemplateView, ListView
from django.template import loader

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.http import HttpResponse, JsonResponse
from django.db import IntegrityError
from django.shortcuts import render_to_response

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from MeetingReports.models import UserProfile, Emails, Reports, Meeting
from django.conf import settings


class IndexView(TemplateView):
    template_name = 'meeting-reports/index.html'

    # form_class = MeetingForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IndexView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        try:
            userprofile = UserProfile.objects.get(user_id=self.request.user.id)
        except UserProfile.DoesNotExist:
            context['error'] = '请先完善资历哦'
        else:
            context['userprofile'] = userprofile
            context['emails'] = Emails.objects.get(group_id=userprofile.group.id)
            menbers = UserProfile.objects.filter(group_id=userprofile.group.id).order_by('sorts', 'user__date_joined')
            duty = None
            menberuser = []
            for menber in menbers:
                menberuser.append(menber.user)
                if menber.duty:
                    duty = menber
            if not duty:
                duty = menbers[0]
            context['duty'] = duty.user
            context['menber'] = menberuser
            try:
                meeting = Meeting.objects.filter(group_id=userprofile.group.id).latest('id')
                context['meeting'] = meeting
                context['todayhavereport'] = (
                    meeting.created_time.strftime('%Y%m%d') == datetime.datetime.today().strftime(
                        '%Y%m%d'))
            except Meeting.DoesNotExist:
                pass
        return context


def get_last_userreport(request):
    request.encoding = 'utf-8'
    user = request.GET['userid']
    meeting = request.GET['meetingid']
    if not user or not meeting:
        return HttpResponse("")
    report = Reports.objects.get(meeting_id=meeting, user_id=user)
    return HttpResponse(report.content)


class MeetingDetailView(DetailView):
    model = Meeting
    template_name = "meeting-reports/detail.html"
    context_object_name = "meeting"
    pk_url_kwarg = 'meeting_id'

    def get_context_data(self, **kwargs):
        context = super(MeetingDetailView, self).get_context_data(**kwargs)
        context['reports'] = Reports.objects.filter(meeting_id=self.get_object().id)
        context['userprofile'] = UserProfile.objects.get(user_id=self.get_object().noter.id)
        return context


class MeetingListView(ListView):
    template_name = "meeting-reports/list.html"

    context_object_name = "meeting"

    def get_queryset(self):
        return Meeting.objects.all().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super(MeetingListView, self).get_context_data(**kwargs)
        context['count'] = Meeting.objects.all().count
        return context


class SendEmail(View):
    @method_decorator(login_required)
    def get(self, request):
        userprofile = UserProfile.objects.get(user_id=request.user.id)
        menbers = UserProfile.objects.filter(group_id=userprofile.group.id).order_by('sorts', 'user__date_joined')

        context, dutyuser, menberstr = {}, None, []
        for menber in menbers:
            menberstr.append(menber.user)
            if menber.duty:
                dutyuser = menber.user
        if not dutyuser:
            dutyuser = menbers[0].user

        context['userprofile'] = userprofile
        context['menber'] = menberstr
        reports = json.loads(request.GET["reports"])
        context['reports'] = reports

        # save meeting
        today = datetime.datetime.today()
        subject = userprofile.departments + '_' + userprofile.group.name + '_MeetingReport_' + today.strftime('%Y%m%d')

        master = userprofile.group.ower
        if request.GET.get("duty"):
            dutyuser = User.objects.get(pk=request.GET["duty"])
            master = dutyuser
        elif request.user.id != dutyuser.id:
            return JsonResponse({
                'success': False,
                'msg': '今天应该【' + dutyuser.username + '】发早会哦~'
            })

        # save meeting
        milestonedate1 = datetime.datetime.strptime(request.GET["milestonedate1"], '%Y-%m-%d')
        milestonedate2 = datetime.datetime.strptime(request.GET["milestonedate2"], '%Y-%m-%d')
        meeting = Meeting(topic=subject, milestone1=request.GET["milestone1"],
                          milestone2=request.GET["milestone2"], milestonedate1=milestonedate1,
                          milestonedate2=milestonedate2, created_time=today,
                          noter_id=dutyuser.id, menber=u' > '.join(o.username for o in menberstr),
                          group_id=userprofile.group.id, master_id=master.id)
        try:
            meeting.save()
        except IntegrityError:
            return JsonResponse({
                'success': False,
                'msg': '今天已经发过早会了哦~'
            })

        # save report
        for value in reports:
            report = Reports(user_id=value.get('user_id'), meeting_id=meeting.id, content=value.get('content'),
                             leave=(value.get('content') == 'leave'))
            report.save()

        # change next user duty
        for index, menber in enumerate(menbers):
            if menber.user.id == dutyuser.id:
                nextuser = menbers[(index + 1) if (index < len(menbers) - 1) else 0]
                nextuser.duty = True
                nextuser.save()
                context['duty'] = nextuser

        context['meeting'] = meeting
        html_content = loader.render_to_string(
            'meeting-reports/mail_template.html', context
        )
        try:
            toemails, ccemails = [], []
            emails = Emails.objects.get(group_id=userprofile.group.id)
            if emails.email:
                toemails.append(emails.email)
            elif emails.contain_menber:
                for menber in menbers:
                    toemails.append(menber.user.email)
            if emails.relist:
                for user in emails.relist.all():
                    toemails.append(user.email)
            if emails.cclist:
                for user in emails.cclist.all():
                    ccemails.append(user.email)
            msg = EmailMultiAlternatives(subject=subject, body=html_content, from_email=settings.EMAIL_HOST_USER,
                                         to=toemails, cc=ccemails)
            # 图片签名（非附件）
            img_data = open('static/img/test.png', 'rb').read()
            html_part = MIMEMultipart(_subtype='related')
            body = MIMEText('', _subtype='html')
            html_part.attach(body)
            img = MIMEImage(img_data, 'jpeg')
            img.add_header('Content-Id', '<email_sign>')
            img.add_header("Content-Disposition", "inline", filename="email_sign")
            html_part.attach(img)
            msg.attach(html_part)

            msg.content_subtype = "html"
            msg.encoding = "utf-8"
            msg.send()
            return JsonResponse({
                'success': True,
                'msg': '操作成功'
            })
        except (RuntimeError, TypeError, NameError):
            return JsonResponse({
                'success': False,
                'msg': 'Unexpected error:' + RuntimeError
            })
        return JsonResponse({
            'success': False,
            'msg': '操作失败'
        })


def handler404(request):
    response = render_to_response('404.html', {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response
