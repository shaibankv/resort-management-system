from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from .models import Guest, FoodCharge, BookedRoom, Expense
from .forms import GuestForm, FoodChargeForm, ExpenseForm
from django.conf import settings
from decimal import Decimal
import datetime

@login_required
def home(request):
    now = timezone.now()
    active_guests_count = Guest.objects.filter(is_checked_out=False).count()
    
    monthly_checkouts = Guest.objects.filter(
        is_checked_out=True,
        check_out_date__year=now.year, 
        check_out_date__month=now.month
    )
    
    guests_checked_out_this_month = monthly_checkouts.count()
    
    revenue_this_month = sum(g.total_bill for g in monthly_checkouts)
    
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Reason', 'Amount (Rs)', 'Shop/Vendor', 'Bill Number'])
        for e in expenses:
            writer.writerow([e.date, e.reason, e.amount, e.shop_name, e.bill_number])
        return response
    context = {
        'active_guests_count': active_guests_count,
        'guests_this_month': guests_checked_out_this_month,
        'revenue_this_month': revenue_this_month,
    }
    return render(request, 'resort/dashboard.html', context)

@login_required
def add_guest(request):
    if request.method == 'POST':
        form = GuestForm(request.POST)
        if form.is_valid():
            guest = form.save()
            
            # Process dynamic room entries
            room_numbers = request.POST.getlist('room_number[]')
            room_types = request.POST.getlist('room_type[]')
            room_rates = request.POST.getlist('room_rate[]')
            
            for i in range(len(room_numbers)):
                if room_numbers[i]:
                    BookedRoom.objects.create(
                        guest=guest,
                        room_number=room_numbers[i],
                        room_type=room_types[i],
                        rate_per_day=Decimal(room_rates[i] or '0.00')
                    )
            
            return redirect('active_guests')
    else:
        form = GuestForm()
    return render(request, 'resort/add_guest.html', {'form': form})

@login_required
def active_guests(request):
    guests = Guest.objects.filter(is_checked_out=False).order_by('-check_in_date')
    return render(request, 'resort/active_guests.html', {'guests': guests})

@login_required
def add_food(request, guest_id):
    guest = get_object_or_404(Guest, id=guest_id, is_checked_out=False)
    if request.method == 'POST':
        item_names = request.POST.getlist('item_name[]')
        quantities = request.POST.getlist('quantity[]')
        rates = request.POST.getlist('rate_per_unit[]')
        
        for i in range(len(item_names)):
            if item_names[i]:
                FoodCharge.objects.create(
                    guest=guest,
                    item_name=item_names[i],
                    quantity=int(quantities[i] or 1),
                    rate_per_unit=Decimal(rates[i] or '0.00')
                )
        return redirect('active_guests')
    
    # We no longer strictly need the Django form for this, 
    # but we can pass it if we want to use some fields manually.
    return render(request, 'resort/add_food.html', {'guest': guest})

@login_required
def edit_guest(request, guest_id):
    guest = get_object_or_404(Guest, id=guest_id, is_checked_out=False)
    
    if request.method == 'POST':
        form = GuestForm(request.POST, instance=guest)
        if form.is_valid():
            guest = form.save()
            
            # Recreate rooms
            guest.bookedroom_set.all().delete()
            room_numbers = request.POST.getlist('room_number[]')
            room_types = request.POST.getlist('room_type[]')
            room_rates = request.POST.getlist('room_rate[]')
            
            for i in range(len(room_numbers)):
                if room_numbers[i]:
                    BookedRoom.objects.create(
                        guest=guest,
                        room_number=room_numbers[i],
                        room_type=room_types[i],
                        rate_per_day=Decimal(room_rates[i] or '0.00')
                    )
            
            # Recreate food
            guest.foodcharge_set.all().delete()
            food_names = request.POST.getlist('food_item_name[]')
            food_quantities = request.POST.getlist('food_quantity[]')
            food_rates = request.POST.getlist('food_rate[]')
            food_dates = request.POST.getlist('food_date[]')
            
            for i in range(len(food_names)):
                if food_names[i]:
                    date_val = food_dates[i] if (i < len(food_dates) and food_dates[i]) else timezone.now().date()
                    FoodCharge.objects.create(
                        guest=guest,
                        item_name=food_names[i],
                        quantity=int(food_quantities[i] or 1),
                        rate_per_unit=Decimal(food_rates[i] or '0.00'),
                        date=date_val
                    )
            
            return redirect('active_guests')
    else:
        form = GuestForm(instance=guest)
        
    return render(request, 'resort/edit_guest.html', {'form': form, 'guest': guest})

from django.core.mail import EmailMessage
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa

@login_required
def checkout(request, guest_id):
    guest = get_object_or_404(Guest, id=guest_id, is_checked_out=False)
    
    if request.method == 'POST':
        guest.check_out_date = timezone.now().date()
        guest.is_checked_out = True
        guest.save()
        
        subject = f"Guest Checkout: {guest.name} at Whispering Willows"
        message = (
            f"A guest has checked out.\n\n"
            f"Resort: Whispering Willows\n"
            f"Guest Name: {guest.name}\n"
            f"Phone: {guest.phone_number}\n"
            f"Adults: {guest.number_of_adults}, Children: {guest.number_of_children}\n"
            f"Check-in: {guest.check_in_date}\n"
            f"Check-out: {guest.check_out_date}\n\n"
            f"Room Bill: ₹{guest.total_room_bill}\n"
            f"Food Bill: ₹{guest.total_food_bill}\n"
            f"Total Bill: ₹{guest.total_bill}\n"
        )
        
        # Generate PDF
        template = get_template('resort/bill_pdf.html')
        html = template.render({'guest': guest})
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
        
        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.RECEIVER_EMAIL],
        )
        if not pdf.err:
            email.attach(f"Bill_{guest.name}.pdf", result.getvalue(), 'application/pdf')
            
        email.send(fail_silently=True)
        
        return render(request, 'resort/checkout_bill.html', {'guest': guest})
    
    guest.check_out_date = timezone.now().date()
    return render(request, 'resort/checkout_confirm.html', {'guest': guest})

@login_required
def view_bill(request, guest_id):
    guest = get_object_or_404(Guest, id=guest_id, is_checked_out=True)
    return render(request, 'resort/checkout_bill.html', {'guest': guest})

@login_required
def visited_guests(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    mode = request.GET.get('mode')
    revenue_type = request.GET.get('revenue_type', 'all')
    
    guests = Guest.objects.filter(is_checked_out=True).order_by('-check_out_date')
    
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            guests = guests.filter(check_out_date__gte=start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            guests = guests.filter(check_out_date__lte=end_date)
        except ValueError:
            pass

    if mode:
        guests = guests.filter(mode_of_booking=mode)
        
    total_revenue = sum(g.total_bill for g in guests)
    total_room_revenue = sum(g.total_room_bill for g in guests)
    total_food_revenue = sum(g.total_food_bill for g in guests)
        
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="visited_guests_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Guest Name', 'Phone', 'Check-in', 'Check-out', 'Room Bill', 'Food Bill', 'Total Bill'])
        for g in guests:
            writer.writerow([g.name, g.phone_number, g.check_in_date, g.check_out_date, g.total_room_bill, g.total_food_bill, g.total_bill])
        return response
        
    elif request.GET.get('export') == 'email':
        subject = "Revenue & Visited Guests Report"
        message = (
            f"Revenue Report - Whispering Willows\n\n"
            f"Period: {start_date_str or 'Beginning'} to {end_date_str or 'Present'}\n"
            f"Mode: {mode or 'All Modes'}\n"
            f"Revenue Type: {revenue_type}\n\n"
            f"Total Room Revenue: ₹{total_room_revenue}\n"
            f"Total Food Revenue: ₹{total_food_revenue}\n"
            f"Grand Total Revenue: ₹{total_revenue}\n\n"
            f"Guests Details:\n"
        )
        for g in guests:
            message += f"- {g.name} | Dates: {g.check_in_date} to {g.check_out_date} | Total Bill: ₹{g.total_bill}\n"
            
        # Generate PDF
        pdf_context = {
            'guests': guests,
            'total_revenue': total_revenue,
            'total_room_revenue': total_room_revenue,
            'total_food_revenue': total_food_revenue,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'mode': mode,
        }
        template = get_template('resort/revenue_report_pdf.html')
        html = template.render(pdf_context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
        
        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.RECEIVER_EMAIL],
        )
        if not pdf.err:
            email.attach("Revenue_Report.pdf", result.getvalue(), 'application/pdf')
            
        email.send(fail_silently=True)
        messages.success(request, 'The Revenue report has been emailed successfully.')
        # Remove export parameter to avoid resending on refresh
        qd = request.GET.copy()
        qd.pop('export', None)
        return redirect(f"{request.path}?{qd.urlencode()}")
    context = {
        'guests': guests,
        'total_revenue': total_revenue,
        'total_room_revenue': total_room_revenue,
        'total_food_revenue': total_food_revenue,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'mode': mode,
        'revenue_type': revenue_type
    }
        
    return render(request, 'resort/visited_guests.html', context)

@login_required
def manage_expenses(request):
    expenses = Expense.objects.all().order_by('-date', '-id')
    return render(request, 'resort/manage_expenses.html', {'expenses': expenses})

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_expenses')
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})
    return render(request, 'resort/add_expense.html', {'form': form})

@login_required
def expense_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    expenses = Expense.objects.all().order_by('-date')
    
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            expenses = expenses.filter(date__gte=start_date)
        except ValueError:
            pass
            
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            expenses = expenses.filter(date__lte=end_date)
        except ValueError:
            pass
            
    total_expense = sum(e.amount for e in expenses)
    
    # Prepare data for Chart.js
    # Group by date
    from collections import defaultdict
    daily_totals = defaultdict(float)
    for e in expenses:
        daily_totals[e.date.strftime('%Y-%m-%d')] += float(e.amount)
        
    dates_list = sorted(daily_totals.keys())
    amounts_list = [daily_totals[d] for d in dates_list]
    
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expense_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Reason', 'Amount (Rs)', 'Shop/Vendor', 'Bill Number'])
        for e in expenses:
            writer.writerow([e.date, e.reason, e.amount, e.shop_name, e.bill_number])
        return response
        
    elif request.GET.get('export') == 'email':
        subject = "Expense Report - Whispering Willows"
        message = (
            f"Expense Report - Whispering Willows\n\n"
            f"Period: {start_date_str or 'Beginning'} to {end_date_str or 'Present'}\n"
            f"Total Expense: ₹{total_expense}\n\n"
            f"Expense Details:\n"
        )
        for e in expenses:
            message += f"- {e.date} | {e.reason} | ₹{e.amount} | {e.shop_name}\n"
            
        # Generate PDF
        pdf_context = {
            'expenses': expenses,
            'total_expense': total_expense,
            'start_date': start_date_str,
            'end_date': end_date_str,
        }
        template = get_template('resort/expense_report_pdf.html')
        html = template.render(pdf_context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
        
        email = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.RECEIVER_EMAIL],
        )
        if not pdf.err:
            email.attach("Expense_Report.pdf", result.getvalue(), 'application/pdf')
            
        email.send(fail_silently=True)
        messages.success(request, 'The Expense report has been emailed successfully.')
        qd = request.GET.copy()
        qd.pop('export', None)
        return redirect(f"{request.path}?{qd.urlencode()}")
        
    context = {
        'expenses': expenses,
        'total_expense': total_expense,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'chart_dates': dates_list,
        'chart_amounts': amounts_list,
    }
    if request.GET.get('export') == 'pdf':
        return render(request, 'resort/expense_report_print.html', context)
    return render(request, 'resort/expense_report.html', context)


