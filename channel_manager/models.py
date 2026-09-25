from django.db import models
from django.utils import timezone
import uuid

class RoomType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name

class PhysicalRoom(models.Model):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('MAINTENANCE', 'Maintenance'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('BLOCKED', 'Blocked'),
    )
    room_number = models.CharField(max_length=50, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    def __str__(self):
        return f"{self.room_number} ({self.room_type.name})"

class Channel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)
    # Store JSON config; mask in UI
    api_credentials = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    )
    
    SOURCE_CHOICES = (
        ('DIRECT', 'Direct'),
        ('WALK_IN', 'Walk-in'),
        ('PHONE', 'Phone'),
        ('OFFLINE', 'Offline'),
        ('BOOKING_COM', 'Booking.com'),
        ('AGODA', 'Agoda'),
        ('MAKEMYTRIP', 'MakeMyTrip'),
        ('EXPEDIA', 'Expedia'),
        ('OTHER_OTA', 'Other OTA'),
    )

    reservation_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    guest = models.ForeignKey('resort.Guest', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservations')
    
    guest_name = models.CharField(max_length=200)
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_email = models.EmailField(blank=True)
    
    external_reservation_id = models.CharField(max_length=100, blank=True, null=True)
    booking_source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='DIRECT')
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    check_in = models.DateField()
    check_out = models.DateField()
    
    number_of_adults = models.IntegerField(default=1)
    number_of_children = models.IntegerField(default=0)
    
    special_requests = models.TextField(blank=True)
    
    payment_status = models.CharField(max_length=20, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    cancellation_date = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    def __str__(self):
        return f"Res {self.reservation_id} - {self.guest_name}"

class SyncLog(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending'),
    )
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    operation = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.channel.name} - {self.operation} - {self.status}"
