from django import forms
from .models import Guest, FoodCharge, Expense

class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = [
            'name', 'phone_number', 'mode_of_booking', 'booked_by', 
            'number_of_adults', 'number_of_children', 'extra_bed_needed', 'extra_bed_rate'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'mode_of_booking': forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_of_booking'}),
            'booked_by': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_booked_by'}),
            'number_of_adults': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'number_of_children': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'extra_bed_needed': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_extra_bed_needed'}),
            'extra_bed_rate': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_extra_bed_rate', 'step': '0.01'}),
        }

class FoodChargeForm(forms.ModelForm):
    class Meta:
        model = FoodCharge
        fields = ['item_name', 'quantity', 'rate_per_unit']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Breakfast, Burger...'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'rate_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'amount', 'reason', 'shop_name', 'bill_number', 'bill_photo']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What was this expense for?'}),
            'shop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'bill_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'bill_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
