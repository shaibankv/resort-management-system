from django.urls import path, include
from resort import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add-guest/', views.add_guest, name='add_guest'),
    path('active-guests/', views.active_guests, name='active_guests'),
    path('edit-guest/<int:guest_id>/', views.edit_guest, name='edit_guest'),
    path('add-food/<int:guest_id>/', views.add_food, name='add_food'),
    path('checkout/<int:guest_id>/', views.checkout, name='checkout'),
    path('view-bill/<int:guest_id>/', views.view_bill, name='view_bill'),
    path('visited-guests/', views.visited_guests, name='visited_guests'),
    path('expenses/', views.manage_expenses, name='manage_expenses'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/report/', views.expense_report, name='expense_report'),
    path('run-migrations/', views.run_migrations, name='run_migrations'),
]
