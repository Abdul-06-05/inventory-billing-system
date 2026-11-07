from django import forms
from django.contrib.auth.models import User

from .models import Category, Product, Purchase, Supplier


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "address"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "price", "stock", "reorder_level"]


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["supplier", "product", "quantity", "cost_price"]


class StaffForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[("staff", "Staff"), ("admin", "Admin")])

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username already exists.")
        return username
