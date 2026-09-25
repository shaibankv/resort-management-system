from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import datetime
from django.db import transaction
from django.contrib import messages

from .models import RoomType, PhysicalRoom, Channel, Reservation, SyncLog
from .availability import AvailabilityEngine
from .sync import trigger_inventory_sync
from resort.models import Guest, BookedRoom

@login_required
def dashboard(request):
    today = timezone.now().date()
    total_rooms = PhysicalRoom.objects.count()
    reservations_today = Reservation.objects.filter(check_in=today).count()
    channels = Channel.objects.all()
    failed_syncs = SyncLog.objects.filter(status='FAILED').count()
    
    context = {
        'total_rooms': total_rooms,
        'reservations_today': reservations_today,
        'channels': channels,
        'failed_syncs': failed_syncs,
    }
    return render(request, 'channel_manager/dashboard.html', context)

@login_required
def reservations(request):
    reservations_list = Reservation.objects.all().order_by('-created_at')
    return render(request, 'channel_manager/reservations.html', {'reservations': reservations_list})

@login_required
def create_reservation(request):
    room_types = RoomType.objects.all()
    if request.method == 'POST':
        guest_name = request.POST.get('guest_name')
        guest_phone = request.POST.get('guest_phone')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        room_type_id = request.POST.get('room_type')
        num_rooms = int(request.POST.get('num_rooms', 1))
        
        check_in_date = datetime.datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.datetime.strptime(check_out, '%Y-%m-%d').date()
        
        rt = get_object_or_404(RoomType, id=room_type_id)
        
        # Concurrency protection / Check availability
        with transaction.atomic():
            # Check availability for the requested period
            is_available = AvailabilityEngine.is_available(rt, check_in_date, check_out_date, num_rooms)
            if not is_available:
                messages.error(request, f"Not enough rooms available for {rt.name} on the selected dates.")
                return redirect('channel_manager:create_reservation')
            
            res = Reservation.objects.create(
                guest_name=guest_name,
                guest_phone=guest_phone,
                check_in=check_in_date,
                check_out=check_out_date,
                booking_status='CONFIRMED',
                booking_source='OFFLINE',
                number_of_adults=1,
            )
            
            # Create BookedRooms belonging to this Reservation (guest=None initially)
            for _ in range(num_rooms):
                BookedRoom.objects.create(
                    reservation=res,
                    room_type=rt.name,
                    room_number="TBD", 
                    rate_per_day=rt.base_price
                )
                
        # Outside transaction, trigger sync
        trigger_inventory_sync(rt, check_in_date, check_out_date)
        messages.success(request, "Reservation created successfully and inventory sync queued.")
        return redirect('channel_manager:reservations')

    return render(request, 'channel_manager/create_reservation.html', {'room_types': room_types})

@login_required
def checkin_reservation(request, res_id):
    reservation = get_object_or_404(Reservation, reservation_id=res_id)
    
    if reservation.booking_status == 'CHECKED_IN':
        messages.warning(request, "Reservation already checked in.")
        return redirect('channel_manager:reservations')
        
    with transaction.atomic():
        guest = Guest.objects.create(
            name=reservation.guest_name,
            phone_number=reservation.guest_phone,
            mode_of_booking=reservation.booking_source[:20],
            booked_by='Channel Manager',
            number_of_adults=reservation.number_of_adults,
            number_of_children=reservation.number_of_children,
            check_in_date=reservation.check_in,
            check_out_date=reservation.check_out,
            is_checked_out=False
        )
        
        reservation.guest = guest
        reservation.booking_status = 'CHECKED_IN'
        reservation.save()
        
        # Link BookedRooms to the actual Guest so existing billing logic works perfectly
        for br in reservation.booked_rooms.all():
            br.guest = guest
            br.save()
            
    messages.success(request, f"Guest {guest.name} successfully checked in!")
    return redirect('active_guests')

@login_required
def calendar_view(request):
    start_date_str = request.GET.get('start_date')
    if start_date_str:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date()
        
    dates = [start_date + timedelta(days=i) for i in range(14)]
    room_types = RoomType.objects.all()
    
    calendar_data = []
    for rt in room_types:
        row = {'room_type': rt.name, 'availability': []}
        for d in dates:
            avail = AvailabilityEngine.get_availability(rt, d)
            row['availability'].append(avail)
        calendar_data.append(row)
        
    return render(request, 'channel_manager/calendar.html', {
        'dates': dates,
        'calendar_data': calendar_data,
        'start_date': start_date.strftime('%Y-%m-%d')
    })

@login_required
def channels(request):
    channels_list = Channel.objects.all()
    return render(request, 'channel_manager/channels.html', {'channels': channels_list})

@login_required
def toggle_channel(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    channel.is_active = not channel.is_active
    channel.save()
    messages.success(request, f"Channel {channel.name} is now {'Active' if channel.is_active else 'Inactive'}.")
    return redirect('channel_manager:channels')

@login_required
def sync_logs(request):
    logs = SyncLog.objects.order_by('-timestamp')[:50]
    return render(request, 'channel_manager/sync_logs.html', {'logs': logs})
