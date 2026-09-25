from django.contrib import admin
from .models import Guest, FoodCharge, Expense

admin.site.register(Guest)
admin.site.register(FoodCharge)
# admin.site.register(BookedRoom)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'reason', 'amount', 'shop_name', 'bill_number')
    list_filter = ('date',)
    search_fields = ('reason', 'shop_name', 'bill_number')
    date_hierarchy = 'date'
