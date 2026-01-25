import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import PromoCode, Procedure


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
        # Получаем данные из URL
    salon_id = request.GET.get("salon")
    procedure_id = request.GET.get("procedure")
    specialist_id = request.GET.get("specialist")
    date_str = request.GET.get("date")
    time_str = request.GET.get("time")

    context = {}
    
    if salon_id:
        context["salon"] = Salon.objects.filter(pk=salon_id).first()
    if procedure_id:
        context["procedure"] = Procedure.objects.filter(pk=procedure_id).first()
    if specialist_id:
        context["specialist"] = Specialist.objects.filter(pk=specialist_id).first()
    
    context.update({
        "date": date_str,
        "time": time_str,
    })

    return render(request, "serviceFinally.html", context)


@csrf_exempt
@require_POST
def validate_promo(request):
    try:
        data = json.loads(request.body)
        code = data.get("promo_code", "").strip()
        procedure_id = data.get("procedure_id")
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Некорректные данные"}, status=400)

    if not procedure_id:
        return JsonResponse({"error": "Не указана процедура"}, status=400)

    # Получаем базовую цену из общей процедуры
    try:
        procedure = Procedure.objects.get(id=procedure_id)
        base_price = procedure.base_price  # Это Decimal!
    except Procedure.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "error": "Процедура не найдена"
        })

    try:
        promo = PromoCode.objects.get(code__iexact=code, is_active=True)
    except PromoCode.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "error": "Промокод не найден или неактивен"
        })

    from datetime import date
    today = date.today()

    if promo.valid_from and promo.valid_from > today:
        return JsonResponse({
            "valid": False,
            "error": "Промокод ещё не активен"
        })
    if promo.valid_to and promo.valid_to < today:
        return JsonResponse({
            "valid": False,
            "error": "Срок действия промокода истёк"
        })

    # Считаем новую цену
    discount = base_price * Decimal(promo.discount_percent) / Decimal(100)
    new_price = (base_price - discount).quantize(Decimal('0.01'))

    return JsonResponse({
        "valid": True,
        "discount_percent": promo.discount_percent,
        "new_price": str(new_price),
        "original_price": str(base_price)
    })