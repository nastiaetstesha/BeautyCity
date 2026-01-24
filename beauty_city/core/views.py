import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from .models import PromoCode


def index(request):
    return render(request, 'index.html')


def admin_page(request):
    return render(request, 'admin.html')


def notes(request):
    return render(request, 'notes.html')


def popup_examples(request):
    return render(request, 'popup.html')


def service(request):
    return render(request, 'service.html')


def service_finally(request):
    return render(request, 'serviceFinally.html')


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

    # Заглушка: базовая цена = 1000 руб.
    base_price = 1000.0

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

    discount = base_price * promo.discount_percent / 100
    new_price = round(base_price - discount, 2)

    return JsonResponse({
        "valid": True,
        "discount_percent": promo.discount_percent,
        "new_price": new_price
    })