from django.contrib.auth.models import User, Group
from django.db import transaction
from django.core.exceptions import ValidationError
from library.models.borrow_models import Member

@transaction.atomic
def register_member(*, data):
    if User.objects.filter(email=data["email"]).exists():
        raise ValidationError("Email already registered")

    user = User.objects.create_user(
        username=data["email"],
        email=data["email"],
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
    )

    user.groups.add(Group.objects.get(name="MEMBER"))

    Member.objects.create(
        user=user,
        is_active=True,
        membership_number=f"MEM-{Member.objects.count() + 1:05d}"
    )

    return user
