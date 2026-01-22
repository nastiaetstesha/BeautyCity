from django.shortcuts import render
from .models import SiteSettings

def get_settings():
    # если настроек ещё нет — вернём None
    return SiteSettings.objects.first()


def index(request):
    return render(request, "index.html", {"settings": get_settings()})


def admin_page(request):
    return render(request, 'admin.html')


def notes(request):
    return render(request, 'notes.html')


def popup_examples(request):
    return render(request, 'popup.html')


def service(request):
    return render(request, "service.html", {"settings": get_settings()})


def service_finally(request):
    return render(request, "serviceFinally.html", {"settings": get_settings()})

