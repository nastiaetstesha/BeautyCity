"""
Создание тестовой записи для проверки оплаты
"""
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_city.settings')
django.setup()

from core.models import Booking, Salon, Procedure, Specialist
from django.utils import timezone

print("🔄 Создание тестовых данных...")

# 1. Создаем или находим салон
salon, created = Salon.objects.get_or_create(
    name="Beauty City Центр",
    defaults={
        'address': 'ул. Тестовая, 10',
        'phone': '+79990001122',
        'is_active': True
    }
)
print(f"✅ Салон: {salon.name}")

# 2. Создаем или находим процедуру
procedure, created = Procedure.objects.get_or_create(
    title="Маникюр + покрытие",
    defaults={
        'base_price': 2500,
        'duration_minutes': 90,
        'description': 'Тестовая процедура для оплаты'
    }
)
print(f"✅ Процедура: {procedure.title} - {procedure.base_price} руб.")

# 3. Создаем или находим специалиста
specialist, created = Specialist.objects.get_or_create(
    full_name="Мария Тестова",
    defaults={
        'bio': 'Специалист по маникюру',
        'experience': '5 лет опыта',
        'is_active': True
    }
)
print(f"✅ Специалист: {specialist.full_name}")

# 4. Создаем запись
from datetime import datetime, timedelta

# Завтра в 14:00
start_time = timezone.now() + timedelta(days=1)
start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)

booking = Booking.objects.create(
    salon=salon,
    procedure=procedure,
    specialist=specialist,
    customer_name="Анна Клиентова",
    phone="+79991234567",
    start_at=start_time,
    end_at=start_time + timedelta(minutes=procedure.duration_minutes),
    price_original=procedure.base_price,
    price_final=procedure.base_price,  # без скидки
    status='new',
    source='web'
)

print("\n🎉 ТЕСТОВАЯ ЗАПИСЬ СОЗДАНА!")
print(f"📋 ID записи: {booking.id}")
print(f"👤 Клиент: {booking.customer_name}")
print(f"📞 Телефон: {booking.phone}")
print(f"💅 Процедура: {booking.procedure.title}")
print(f"💰 Стоимость: {booking.price_final} руб.")
print(f"📅 Дата: {booking.start_at.strftime('%d.%m.%Y %H:%M')}")
print(f"🏠 Салон: {booking.salon.name}")
print(f"👩‍🎨 Специалист: {booking.specialist.full_name}")

print("\n🔗 Ссылка для оплаты:")
print(f"http://localhost:8000/create-payment/{booking.id}/")
print("\n📋 Для проверки в админке:")
print(f"http://localhost:8000/admin/core/booking/{booking.id}/change/")
