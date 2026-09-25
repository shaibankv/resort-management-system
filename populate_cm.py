import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resort_project.settings')
django.setup()

from channel_manager.models import RoomType, PhysicalRoom, Channel

def populate():
    # Channels
    Channel.objects.get_or_create(name='Booking.com', defaults={'is_active': True})
    Channel.objects.get_or_create(name='Agoda', defaults={'is_active': False})
    Channel.objects.get_or_create(name='MakeMyTrip', defaults={'is_active': True})

    # Room Types
    deluxe, _ = RoomType.objects.get_or_create(name='Deluxe Room', defaults={'base_price': 5000})
    premium, _ = RoomType.objects.get_or_create(name='Premium Room', defaults={'base_price': 8000})

    # Physical Rooms
    PhysicalRoom.objects.get_or_create(room_number='101', defaults={'room_type': deluxe})
    PhysicalRoom.objects.get_or_create(room_number='102', defaults={'room_type': deluxe})
    PhysicalRoom.objects.get_or_create(room_number='103', defaults={'room_type': deluxe})
    
    PhysicalRoom.objects.get_or_create(room_number='201', defaults={'room_type': premium})
    PhysicalRoom.objects.get_or_create(room_number='202', defaults={'room_type': premium})
    
    print("Populated test data.")

if __name__ == '__main__':
    populate()
