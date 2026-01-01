from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes

@permission_classes([])
def connect_facebook_page(request):
    return render(request, "connect_facebook.html")

def post_generate(request):
    return render(request, "post_generate.html")

def login(request):
    return render(request, "login.html")
