from django.shortcuts import render


def join(request):
    return render(request, 'authapp/sign_up.html', {})