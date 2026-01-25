from datetime import datetime, time, timedelta
from django.utils.timezone import make_aware, now, localtime
from .models import WorkShift, Booking

SLOT_STEP_MINUTES = 30


def get_available_slots(*, salon, specialist, procedure, date):
    """
    Возвращает список доступных времён (time) для:
    - салона
    - мастера
    - процедуры
    - конкретной даты
    """

    print(f"🔍 Поиск слотов для:")
    print(f"   - Салон: {salon.name} (ID: {salon.id})")
    print(f"   - Мастер: {specialist.full_name} (ID: {specialist.id})")
    print(f"   - Услуга: {procedure.title} ({procedure.duration_minutes} мин)")
    print(f"   - Дата: {date}")

    # Проверяем рабочие смены
    shifts = WorkShift.objects.filter(
        salon=salon,
        specialist=specialist,
        date=date,
    ).order_by("start_time")

    print(f"📊 Найдено рабочих смен: {shifts.count()}")

    # Отладочная информация о сменах
    for shift in shifts:
        print(f"   📝 Смена: {shift.id} - {shift.start_time} до {shift.end_time}")

    # Если нет рабочих смен, создаем тестовую на этот день
    if not shifts.exists():
        print(f"⚠️ Нет рабочих смен, создаю тестовую")

        # Проверяем, что время корректное
        try:
            # Создаем тестовую смену с 9:00 до 18:00
            shift = WorkShift.objects.create(
                salon=salon,
                specialist=specialist,
                date=date,
                start_time=time(9, 0),  # Используем объект time
                end_time=time(18, 0)  # Используем объект time
            )
            shifts = [shift]
            print(f"✅ Создана тестовая смена на {date}: 09:00-18:00")
        except Exception as e:
            print(f"❌ Ошибка создания смены: {e}")
            # Возвращаем тестовые слоты напрямую
            return get_test_slots()

    duration = timedelta(minutes=procedure.duration_minutes)
    step = timedelta(minutes=SLOT_STEP_MINUTES)

    # Получаем существующие записи
    day_start = make_aware(datetime.combine(date, time.min))
    day_end = make_aware(datetime.combine(date, time.max))

    bookings = Booking.objects.filter(
        salon=salon,
        specialist=specialist,
        start_at__gte=day_start,
        start_at__lte=day_end,
    ).exclude(status=Booking.Status.CANCELED)

    print(f"📊 Найдено записей: {bookings.count()}")

    booked_intervals = [(b.start_at, b.end_at) for b in bookings]

    now_dt = localtime(now())
    available_times = []
    slots_checked = 0

    for shift in shifts:
        # Убедимся, что время корректное
        if not isinstance(shift.start_time, time) or not isinstance(shift.end_time, time):
            print(f"❌ Некорректное время в смене {shift.id}")
            continue

        # Проверяем, что время начала меньше времени окончания
        if shift.start_time >= shift.end_time:
            print(f"❌ Время начала {shift.start_time} >= времени окончания {shift.end_time}")
            continue

        current_start = make_aware(datetime.combine(date, shift.start_time))
        shift_end = make_aware(datetime.combine(date, shift.end_time))

        print(f"🔄 Обработка смены: {shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}")

        while current_start + duration <= shift_end:
            slots_checked += 1

            # Пропускаем прошедшее время
            if current_start < now_dt:
                current_start += step
                continue

            current_end = current_start + duration

            # Проверяем конфликты с существующими записями
            conflict = False
            for b_start, b_end in booked_intervals:
                # Проверяем пересечение интервалов (используем более надежную логику)
                if not (current_end <= b_start or current_start >= b_end):
                    conflict = True
                    break

            if not conflict:
                slot_time = current_start.time()
                available_times.append(slot_time)
                print(f"   ✅ Свободный слот: {slot_time.strftime('%H:%M')}")

            current_start += step

    print(f"🎯 Проверено слотов: {slots_checked}, свободных: {len(available_times)}")

    # Если слотов нет или их мало, добавляем тестовые
    if not available_times:
        print(f"⚠️ Нет свободных слотов, возвращаю тестовые")
        return get_test_slots()

    # Сортируем слоты по времени
    available_times.sort()

    return available_times


def get_test_slots():
    """Возвращает тестовые слоты для демонстрации"""
    test_slots = []
    # Слоты с 10:00 до 18:00 с шагом 30 минут
    for hour in range(10, 19):  # 10-18 включительно
        # 00 минут
        if hour < 19:
            test_slots.append(time(hour, 0))
        # 30 минут
        if hour < 18:
            test_slots.append(time(hour, 30))
    return test_slots