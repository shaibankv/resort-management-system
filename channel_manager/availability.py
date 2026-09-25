from datetime import timedelta
from django.utils import timezone
from channel_manager.models import RoomType, PhysicalRoom, Reservation
from resort.models import BookedRoom

class AvailabilityEngine:
    @staticmethod
    def get_availability(room_type, target_date):
        """
        Calculate available inventory for a specific room type on a specific date.
        """
        # 1. Base Sellable Inventory
        # We only count physical rooms that are currently AVAILABLE.
        sellable_rooms = PhysicalRoom.objects.filter(
            room_type=room_type,
            status='AVAILABLE'
        ).count()

        # 2. Count rooms booked via Reservations
        # A reservation occupies a room for nights: check_in <= target_date < check_out
        active_reservations = Reservation.objects.filter(
            booking_status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN'],
            check_in__lte=target_date,
            check_out__gt=target_date
        )
        
        # How many BookedRooms for this room_type belong to these reservations?
        # We check both the string `room_type` name (for compatibility) or linked physical room.
        res_booked = BookedRoom.objects.filter(
            reservation__in=active_reservations,
            room_type=room_type.name
        ).count()

        # 3. Count rooms booked via legacy Guests (who don't have a Reservation object)
        # For legacy guests, if they are not checked out and check_in_date <= target_date, they occupy the room.
        # If they have a check_out_date in the past but is_checked_out=False, we still consider them occupying today.
        legacy_booked = BookedRoom.objects.filter(
            reservation__isnull=True,
            guest__isnull=False,
            room_type=room_type.name,
            guest__is_checked_out=False,
            guest__check_in_date__lte=target_date
        ).count()

        total_booked = res_booked + legacy_booked
        available = sellable_rooms - total_booked
        return max(0, available)

    @staticmethod
    def get_availability_range(room_type, start_date, end_date):
        """
        Get a dictionary of availability for a range of dates.
        """
        availability = {}
        current_date = start_date
        while current_date <= end_date:
            availability[current_date] = AvailabilityEngine.get_availability(room_type, current_date)
            current_date += timedelta(days=1)
        return availability

    @staticmethod
    def is_available(room_type, check_in, check_out, num_rooms=1):
        """
        Check if num_rooms are available for the entire duration.
        """
        current_date = check_in
        while current_date < check_out:
            if AvailabilityEngine.get_availability(room_type, current_date) < num_rooms:
                return False
            current_date += timedelta(days=1)
        return True
