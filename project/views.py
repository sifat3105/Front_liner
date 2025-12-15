from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def connect_facebook_page(request):
    return render(request, "connect_facebook.html")
