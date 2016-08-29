#!/usr/bin/env python
# coding=utf-8
from MeetingReports.models import Meeting
from django.forms import ModelForm, DateInput
from django.core.exceptions import NON_FIELD_ERRORS


class DateInput(DateInput):
    format_key = 'DATE_INPUT_FORMATS'
    input_type = 'date'


class MeetingForm(ModelForm):
    class Meta:
        model = Meeting

        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }

        fields = ('milestone1', 'milestone2', 'milestonedate1', 'milestonedate2')

        widgets = {
            'milestonedate1': DateInput(attrs={'class': '',
                                               'placeholder': 'Select a date'}
                                        ),
            'milestonedate2': DateInput(attrs={'class': '',
                                               'placeholder': 'Select a date'}
                                        ),
        }
