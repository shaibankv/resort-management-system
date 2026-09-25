from django.db import models
from django.utils import timezone
from decimal import Decimal

class Guest(models.Model):
    MODE_CHOICES = (
        ('Online', 'Online'),
        ('Offline', 'Offline'),
    )

    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    mode_of_booking = models.CharField(max_length=20, choices=MODE_CHOICES)
    booked_by = models.CharField(max_length=200, blank=True, null=True, help_text="Required if offline")
    
    number_of_adults = models.IntegerField(default=1)
    number_of_children = models.IntegerField(default=0)
    extra_bed_needed = models.BooleanField(default=False)
    extra_bed_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    check_in_date = models.DateField(default=timezone.now)
    check_out_date = models.DateField(blank=True, null=True)
    is_checked_out = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.phone_number}"

    @property
    def daily_room_rate(self):
        base_daily_rate = sum(room.rate_per_day for room in self.bookedroom_set.all())
        
        if self.extra_bed_needed:
            base_daily_rate += self.extra_bed_rate
            
        return base_daily_rate

    @property
    def total_room_bill(self):
        if not self.check_out_date:
            return Decimal('0.00')
        days = (self.check_out_date - self.check_in_date).days
        if days <= 0:
            days = 1
            
        return self.daily_room_rate * days

    @property
    def total_food_bill(self):
        return sum(order.total_amount for order in self.foodcharge_set.all())

    @property
    def total_bill(self):
        return self.total_room_bill + self.total_food_bill


class BookedRoom(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, blank=True)
    reservation = models.ForeignKey('channel_manager.Reservation', on_delete=models.CASCADE, null=True, blank=True, related_name='booked_rooms')
    physical_room = models.ForeignKey('channel_manager.PhysicalRoom', on_delete=models.SET_NULL, null=True, blank=True)
    
    room_type = models.CharField(max_length=100)
    room_number = models.CharField(max_length=50)
    rate_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.room_number} ({self.room_type}) - ₹{self.rate_per_day}"


class FoodCharge(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=255, default='Food Item')
    quantity = models.IntegerField(default=1)
    rate_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    date = models.DateField(default=timezone.now)

    @property
    def total_amount(self):
        return self.quantity * self.rate_per_unit

    def __str__(self):
        return f"{self.quantity}x {self.item_name} for {self.guest.name}"

class Expense(models.Model):
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=255)
    shop_name = models.CharField(max_length=255, blank=True, null=True)
    bill_number = models.CharField(max_length=100, blank=True, null=True)
    bill_photo = models.FileField(upload_to='expense_bills/', blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.reason} - ₹{self.amount}"
