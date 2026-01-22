from django.shortcuts import render
from .models import Salon, Procedure, Specialist


def index(request):
    salons = Salon.objects.filter(is_active=True)
    procedures = Procedure.objects.all()
    specialists = Specialist.objects.filter(is_active=True).prefetch_related("procedures")

    return render(request, "index.html", {
        "salons": salons,
        "procedures": procedures,
        "specialists": specialists,
    })


def admin_page(request):
    return render(request, "admin.html")


def notes(request):
    return render(request, "notes.html")


def popup_examples(request):
    return render(request, "popup.html")


def service(request):
    return render(request, "service.html")


def service_finally(request):
    return render(request, "serviceFinally.html")
