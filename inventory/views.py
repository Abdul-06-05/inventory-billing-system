import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Q, Sum
from django.db.models.functions import TruncDate
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import (CategoryForm, ProductForm, PurchaseForm, StaffForm,
                    SupplierForm)
from .models import (Category, Customer, Invoice, InvoiceItem, Product,
                     Profile, Purchase, Supplier)


# ---------- small helpers (avoid repeating code) ----------

def _save_form(request, form_class, title, back_name, instance=None):
    """Generic add/edit page: shows a form, saves it, goes back to the list."""
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Saved successfully.")
        return redirect(back_name)
    return render(request, "form.html",
                  {"form": form, "title": title, "back_name": back_name})


def _delete(request, model, pk, back_name):
    """Generic delete. PROTECT in models stops deleting rows used elsewhere."""
    obj = get_object_or_404(model, pk=pk)
    try:
        obj.delete()
        messages.success(request, "Deleted.")
    except ProtectedError:
        messages.error(request, "Cannot delete: it is used in other records.")
    return redirect(back_name)


# ---------- dashboard ----------

@login_required
def dashboard(request):
    today = timezone.localdate()
    todays_invoices = Invoice.objects.filter(date__date=today)
    context = {
        "product_count": Product.objects.count(),
        "invoices_today": todays_invoices.count(),
        "sales_today": todays_invoices.aggregate(t=Sum("total"))["t"] or 0,
        # F("reorder_level") compares two columns of the same row in SQL
        "low_stock": Product.objects.filter(stock__lte=F("reorder_level")),
        "recent_invoices": Invoice.objects.select_related("customer")[:5],
    }
    return render(request, "dashboard.html", context)


# ---------- categories ----------

@login_required
def category_list(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category added.")
        return redirect("category_list")
    return render(request, "category_list.html",
                  {"form": form, "categories": Category.objects.all()})


@admin_required
@require_POST
def category_delete(request, pk):
    return _delete(request, Category, pk, "category_list")


# ---------- suppliers ----------

@login_required
def supplier_list(request):
    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Supplier added.")
        return redirect("supplier_list")
    return render(request, "supplier_list.html",
                  {"form": form, "suppliers": Supplier.objects.all()})


@admin_required
@require_POST
def supplier_delete(request, pk):
    return _delete(request, Supplier, pk, "supplier_list")


# ---------- products ----------

@login_required
def product_list(request):
    products = Product.objects.select_related("category")
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(category__name__icontains=q))
    if cat:
        products = products.filter(category_id=cat)
    return render(request, "product_list.html", {
        "products": products, "categories": Category.objects.all(),
        "q": q, "selected_category": cat,
    })


@login_required
def product_create(request):
    return _save_form(request, ProductForm, "Add Product", "product_list")


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return _save_form(request, ProductForm, "Edit Product", "product_list", product)


@admin_required
@require_POST
def product_delete(request, pk):
    return _delete(request, Product, pk, "product_list")


# ---------- purchases (stock in) ----------

@login_required
def purchase_list(request):
    purchases = Purchase.objects.select_related("supplier", "product")[:50]
    return render(request, "purchase_list.html", {"purchases": purchases})


@login_required
def purchase_create(request):
    return _save_form(request, PurchaseForm, "Add Purchase (Stock In)", "purchase_list")


# ---------- billing ----------

class BillingError(Exception):
    """Raised for any problem we want to show to the user (rolls back the bill)."""


@login_required
def billing(request):
    products = [
        {"id": p.id, "name": p.name, "price": float(p.price), "stock": p.stock}
        for p in Product.objects.filter(stock__gt=0).order_by("name")
    ]
    return render(request, "billing.html", {"products": products})


@login_required
@require_POST
def create_invoice(request):
    """Receives the cart as JSON, saves invoice + items, reduces stock.

    Everything is inside transaction.atomic(): if any item fails
    (e.g. not enough stock) the whole bill is rolled back.
    """
    try:
        data = json.loads(request.body)
        rows = data.get("items", [])
        if not rows:
            raise BillingError("Add at least one item.")

        gst = Decimal(str(data.get("gst_percent", "18")))
        if not (0 <= gst <= 100):
            raise BillingError("GST must be between 0 and 100.")

        with transaction.atomic():
            customer = None
            name = str(data.get("customer_name", "")).strip()
            if name:
                customer = Customer.objects.create(
                    name=name, phone=str(data.get("customer_phone", "")).strip())

            invoice = Invoice.objects.create(
                customer=customer, created_by=request.user, gst_percent=gst)

            for row in rows:
                qty = int(row["quantity"])
                if qty <= 0:
                    raise BillingError("Quantity must be at least 1.")
                # lock the product row so two bills cannot sell the same stock
                product = Product.objects.select_for_update().get(pk=row["product_id"])
                if product.stock < qty:
                    raise BillingError(
                        f"Only {product.stock} left for {product.name}.")
                InvoiceItem.objects.create(
                    invoice=invoice, product=product, quantity=qty,
                    price=product.price)  # price taken from DB, not from browser
                product.stock -= qty
                product.save(update_fields=["stock"])

            invoice.calculate_totals()

    except BillingError as err:
        return JsonResponse({"error": str(err)}, status=400)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found."}, status=400)
    except (ValueError, KeyError, TypeError, InvalidOperation, AttributeError):
        return JsonResponse({"error": "Invalid bill data."}, status=400)

    return JsonResponse({"url": reverse("invoice_detail", args=[invoice.pk])})


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related("customer", "created_by")[:100]
    return render(request, "invoice_list.html", {"invoices": invoices})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("customer", "created_by")
        .prefetch_related("items__product"), pk=pk)
    return render(request, "invoice_detail.html", {"invoice": invoice})


# ---------- reports (admin only) ----------

@admin_required
def reports(request):
    today = timezone.localdate()
    try:
        start = datetime.strptime(request.GET["start"], "%Y-%m-%d").date()
        end = datetime.strptime(request.GET["end"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        start, end = today - timedelta(days=29), today

    invoices = Invoice.objects.filter(date__date__gte=start, date__date__lte=end)

    # SQL: SELECT date, SUM(total) ... GROUP BY date
    daily = (invoices.annotate(day=TruncDate("date"))
             .values("day").annotate(total=Sum("total")).order_by("day"))
    # SQL: SELECT product, SUM(quantity) ... GROUP BY product ORDER BY 2 DESC
    top_products = (InvoiceItem.objects.filter(invoice__in=invoices)
                    .values("product__name").annotate(qty=Sum("quantity"))
                    .order_by("-qty")[:5])

    return render(request, "reports.html", {
        "start": start, "end": end,
        "invoice_count": invoices.count(),
        "total_sales": invoices.aggregate(t=Sum("total"))["t"] or 0,
        "top_products": top_products,
        "chart_labels": [d["day"].strftime("%d %b") for d in daily],
        "chart_values": [float(d["total"]) for d in daily],
    })


# ---------- staff management (admin only) ----------

@admin_required
def staff_list(request):
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "staff_list.html", {"users": users})


@admin_required
def staff_create(request):
    form = StaffForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(username=d["username"], password=d["password"])
        Profile.objects.create(user=user, role=d["role"])
        messages.success(request, "User created.")
        return redirect("staff_list")
    return render(request, "form.html",
                  {"form": form, "title": "Add Staff / Admin", "back_name": "staff_list"})
