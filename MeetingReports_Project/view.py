from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import authenticate, login
from MeetingReports_Project.forms import RegisterForm


# Create your views here.
def indexview(request):
    return render(request, 'home.html')


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('/')

    def form_valid(self, form):
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super(RegisterView, self).form_valid(form)
