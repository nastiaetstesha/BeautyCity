from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import Salon, Procedure, Specialist, SiteSettings
from .slots import get_available_slots


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
    salons = Salon.objects.filter(is_active=True)
    procedures = Procedure.objects.all()
    specialists = Specialist.objects.filter(is_active=True)

    salon_id = request.GET.get("salon")
    procedure_id = request.GET.get("procedure")
    specialist_id = request.GET.get("specialist")
    date_str = request.GET.get("date")

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    selected_salon = Salon.objects.filter(pk=salon_id).first() if salon_id else None
    selected_procedure = Procedure.objects.filter(pk=procedure_id).first() if procedure_id else None
    selected_specialist = Specialist.objects.filter(pk=specialist_id).first() if specialist_id else None

    context = {
        "salons": salons,
        "procedures": procedures,
        "specialists": specialists,
        "selected_date": selected_date,
        "selected_salon_id": salon_id,
        "selected_procedure_id": procedure_id,
        "selected_specialist_id": specialist_id,
        "selected_salon": selected_salon,
        "selected_procedure": selected_procedure,
        "selected_specialist": selected_specialist,
    }

    if salon_id and procedure_id and specialist_id:
        salon = get_object_or_404(Salon, pk=salon_id)
        procedure = get_object_or_404(Procedure, pk=procedure_id)
        specialist = get_object_or_404(Specialist, pk=specialist_id)

        slots = get_available_slots(
            salon=salon,
            specialist=specialist,
            procedure=procedure,
            date=selected_date,
        )
        context["time_slots"] = slots

    return render(request, "service.html", context)


def service_finally(request):
    return render(request, "serviceFinally.html")
