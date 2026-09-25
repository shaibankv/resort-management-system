import threading
from .models import Channel, SyncLog
from .adapters import MockOTAAdapter
from .availability import AvailabilityEngine

def get_adapter(channel):
    # Future: return BookingComAdapter(channel), AgodaAdapter(channel) based on channel.name
    return MockOTAAdapter(channel)

def sync_inventory_task(room_type, start_date, end_date):
    channels = Channel.objects.filter(is_active=True)
    if not channels.exists():
        return
        
    availability = AvailabilityEngine.get_availability_range(room_type, start_date, end_date)
    
    for channel in channels:
        adapter = get_adapter(channel)
        log = SyncLog.objects.create(
            channel=channel,
            operation=f"Update Inventory: {room_type.name} from {start_date} to {end_date}",
            status='PENDING'
        )
        try:
            adapter.update_inventory(room_type, start_date, end_date, availability)
            log.status = 'SUCCESS'
            log.save()
        except Exception as e:
            log.status = 'FAILED'
            log.error_message = str(e)
            log.save()

def trigger_inventory_sync(room_type, start_date, end_date):
    """
    Spawns a background thread to sync inventory so it doesn't block the request.
    In a real production environment, use Celery or Redis Queue.
    """
    thread = threading.Thread(target=sync_inventory_task, args=(room_type, start_date, end_date))
    thread.daemon = True
    thread.start()
