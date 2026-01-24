from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('admin-page/', views.admin_page, name='admin_page'),
    path('notes/', views.notes, name='notes'),
    path('popups/', views.popup_examples, name='popup_examples'),

    path('service/', views.service, name='service'),
    path('service/finally/', views.service_finally, name='service_finally'),
    path('api/validate-promo/', views.validate_promo, name='validate_promo'),
]
