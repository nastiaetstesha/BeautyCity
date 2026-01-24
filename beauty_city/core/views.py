import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from .models import PromoCode, ProcedureOffering


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
        procedure_offering_id = data.get("procedure_offering_id")
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Некорректные данные"}, status=400)

    if not procedure_offering_id:
        return JsonResponse({"error": "Не указана услуга"}, status=400)

    # Получаем реальную цену из базы
    try:
        offering = ProcedureOffering.objects.get(id=procedure_offering_id)
        base_price = float(offering.price)
    except ProcedureOffering.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "error": "Услуга не найдена"
        })

    # Проверяем промокод
    try:
        promo = PromoCode.objects.get(code__iexact=code, is_active=True)
    except PromoCode.DoesNotExist:
        return JsonResponse({
            "valid": False,
            "error": "Промокод не найден или неактивен"
        })

    # Считаем новую цену
    discount = base_price * promo.discount_percent / 100
    new_price = round(base_price - discount, 2)

    return JsonResponse({
        "valid": True,
        "discount_percent": promo.discount_percent,
        "new_price": new_price,
        "original_price": base_price
    })