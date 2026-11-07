from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F


class Profile(models.Model):
    """Adds a role (admin / staff) to Django's built-in User."""

    ROLE_CHOICES = [("admin", "Admin"), ("staff", "Staff")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="staff")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)

    @property
    def is_low_stock(self):
        return self.stock <= self.reorder_level

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    """Stock-in: buying products from a supplier increases stock."""

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # F() updates stock in the database itself, so it is safe
            # even if two purchases happen at the same time.
            Product.objects.filter(pk=self.product_id).update(
                stock=F("stock") + self.quantity
            )

    def __str__(self):
        return f"{self.product} x {self.quantity}"


class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("18.00"))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def calculate_totals(self):
        """Call after all InvoiceItems are saved."""
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.gst_amount = (self.subtotal * self.gst_percent / 100).quantize(Decimal("0.01"))
        self.total = self.subtotal + self.gst_amount
        self.save()

    def __str__(self):
        return f"Invoice #{self.pk}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of sale

    @property
    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product} x {self.quantity}"
