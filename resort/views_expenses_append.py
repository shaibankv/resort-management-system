
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
    
    context = {
        'expenses': expenses,
        'total_expense': total_expense,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'chart_dates': dates_list,
        'chart_amounts': amounts_list,
    }
    return render(request, 'resort/expense_report.html', context)
