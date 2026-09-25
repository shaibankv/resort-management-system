from django.urls import path
from . import views

app_name = 'channel_manager'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reservations/', views.reservations, name='reservations'),
    path('reservations/create/', views.create_reservation, name='create_reservation'),
    path('reservations/<str:res_id>/checkin/', views.checkin_reservation, name='checkin'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('channels/', views.channels, name='channels'),
    path('channels/toggle/<int:channel_id>/', views.toggle_channel, name='toggle_channel'),
    path('logs/', views.sync_logs, name='logs'),
]
