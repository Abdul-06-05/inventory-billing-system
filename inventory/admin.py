from django.contrib import admin

from .models import (Category, Customer, Invoice, InvoiceItem, Product,
                     Profile, Purchase, Supplier)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "reorder_level")
    search_fields = ("name",)
    list_filter = ("category",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "total", "created_by", "date")
    inlines = [InvoiceItemInline]


admin.site.register([Profile, Category, Supplier, Purchase, Customer])
