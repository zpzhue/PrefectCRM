from django.shortcuts import render, redirect, reverse
from django.contrib import auth
from django.views import View

from rbac.services.login_init import permission_init
# Create your views here.


class LoginView(View):

    def get(self, request):
        return render(request, "crm/login.html")

    def post(self, request):
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = auth.authenticate(username=username, password=password)

        if user:
            auth.login(request, user)
            request.session['user_id'] = user.pk
            permission_init(request, user)
            return redirect(reverse('index'))
        else:
            return render(request, 'crm/login.html')



def logout(request):
    request.session.flush()
    return redirect("/login/")

def index(request):
    return render(request, "crm/index.html")