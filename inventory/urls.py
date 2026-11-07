from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", views.dashboard, name="dashboard"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/<int:pk>/delete/", views.supplier_delete, name="supplier_delete"),

    path("products/", views.product_list, name="product_list"),
    path("products/add/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),

    path("purchases/", views.purchase_list, name="purchase_list"),
    path("purchases/add/", views.purchase_create, name="purchase_create"),

    path("billing/", views.billing, name="billing"),
    path("billing/save/", views.create_invoice, name="create_invoice"),
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),

    path("reports/", views.reports, name="reports"),
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/add/", views.staff_create, name="staff_create"),
]
