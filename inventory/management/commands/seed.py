from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from inventory.models import Category, Product, Profile, Supplier


class Command(BaseCommand):
    help = "Create demo users and sample data (for development only)."

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser("admin", password="admin123")
            Profile.objects.create(user=admin, role="admin")
        if not User.objects.filter(username="staff").exists():
            staff = User.objects.create_user("staff", password="staff123")
            Profile.objects.create(user=staff, role="staff")

        samples = {
            "Groceries": [("Rice 1kg", 60, 50), ("Sugar 1kg", 45, 8), ("Tea 250g", 120, 30)],
            "Stationery": [("Notebook", 40, 100), ("Pen", 10, 5)],
        }
        for cat_name, items in samples.items():
            cat, _ = Category.objects.get_or_create(name=cat_name)
            for name, price, stock in items:
                Product.objects.get_or_create(
                    name=name, category=cat,
                    defaults={"price": price, "stock": stock, "reorder_level": 10})
        Supplier.objects.get_or_create(name="Sample Supplier", defaults={"phone": "9999999999"})
        self.stdout.write(self.style.SUCCESS(
            "Seeded. Login: admin/admin123 (admin) or staff/staff123 (staff)."))
