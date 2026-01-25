import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime
from .models import Salon, Procedure, Specialist, SiteSettings, Booking, PromoCode
from .slots import get_available_slots
from .forms import BookingForm


def index(request):
    """Главная страница"""
    return render(request, "index.html", {
        "salons": Salon.objects.filter(is_active=True),
        "procedures": Procedure.objects.all(),
        "specialists": Specialist.objects.filter(is_active=True).prefetch_related("procedures"),
    })


def admin_page(request):
    """Админ-панель"""
    return render(request, "admin.html")


def notes(request):
    """Личный кабинет с записями"""
    return render(request, "notes.html")


def popup_examples(request):
    """Примеры всплывающих окон"""
    return render(request, "popup.html")


def service(request):
    """Страница записи на услугу"""
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

    selected_salon = get_object_or_404(Salon, pk=salon_id) if salon_id else None
    selected_procedure = get_object_or_404(Procedure, pk=procedure_id) if procedure_id else None
    selected_specialist = get_object_or_404(Specialist, pk=specialist_id) if specialist_id else None

    time_slots = None
    if all([salon_id, procedure_id, specialist_id]):
        time_slots = get_available_slots(
            salon=selected_salon,
            specialist=selected_specialist,
            procedure=selected_procedure,
            date=selected_date,
        )

    return render(request, "service.html", {
        "salons": salons,
        "procedures": procedures,
        "specialists": specialists,
        "selected_date": selected_date,
        "selected_salon": selected_salon,
        "selected_procedure": selected_procedure,
        "selected_specialist": selected_specialist,
        "time_slots": time_slots,
        "selected_salon_id": salon_id,
        "selected_procedure_id": procedure_id,
        "selected_specialist_id": specialist_id,
    })


def service_finally(request):
    """Подтверждение записи и оплата"""
    # Получаем параметры из URL
    salon_id = request.GET.get('salon')
    procedure_id = request.GET.get('procedure')
    specialist_id = request.GET.get('specialist')
    date_str = request.GET.get('date')
    time_str = request.GET.get('time')

    # Проверяем, что все параметры есть
    if not all([salon_id, procedure_id, specialist_id, date_str, time_str]):
        return redirect('service')

    try:
        # Получаем объекты
        salon = Salon.objects.get(id=salon_id)
        procedure = Procedure.objects.get(id=procedure_id)
        specialist = Specialist.objects.get(id=specialist_id)
    except (Salon.DoesNotExist, Procedure.DoesNotExist, Specialist.DoesNotExist):
        return redirect('service')

    if request.method == 'POST':
        form = BookingForm(request.POST)

        if form.is_valid():
            # Создаем объект записи
            booking = form.save(commit=False)

            # Устанавливаем обязательные поля
            booking.salon = salon
            booking.procedure = procedure
            booking.specialist = specialist
            booking.status = 'new'
            booking.source = 'web'

            # Устанавливаем дату и время
            start_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            booking.start_at = timezone.make_aware(start_at)
            booking.end_at = booking.start_at + timezone.timedelta(
                minutes=procedure.duration_minutes
            )

            # УСТАНАВЛИВАЕМ ЦЕНЫ
            booking.price_original = procedure.base_price
            booking.price_final = procedure.base_price

            booking.save()

            # Перенаправляем на оплату
            return redirect('create_payment', booking_id=booking.id)
    else:
        # GET запрос - создаем предзаполненную форму
        initial_data = {
            'salon': salon_id,
            'procedure': procedure_id,
            'specialist': specialist_id,
            'customer_name': '',
            'phone': '',
            'question': '',
        }
        form = BookingForm(initial=initial_data)

    return render(request, "serviceFinally.html", {
        'form': form,
        'selected_salon': salon,
        'selected_procedure': procedure,
        'selected_specialist': specialist,
        'selected_date': date_str,
        'selected_time': time_str,
    })


@csrf_exempt
@require_POST
def validate_promo(request):
    """Валидация промокода"""
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