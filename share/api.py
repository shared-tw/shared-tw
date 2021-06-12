import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from ninja import Router, errors

from . import models, pagination, schemas

logger = logging.getLogger(__name__)
router = Router()

User = get_user_model()


@router.get(
    "/required-items/",
    auth=None,
    response=pagination.PaginatedResponseSchema[schemas.RequiredItem],
)
def list_required_items(request, page: int = 1):
    items = models.RequiredItem.objects.all()
    return pagination.render(
        request, items=items, schema_cls=schemas.RequiredItem, page=page
    )


def validate_password(password: str, confirmed_password: str, user):
    if password != confirmed_password:
        raise errors.HttpError(422, "Password is not matched.")
    elif len(password) < 8:
        raise errors.HttpError(
            422, "The length of password should be greater than 8 characters."
        )

    django_validate_password(password, user)


@router.post("/register/organization/", auth=None, response=schemas.Organization)
def create_organization(request, payload: schemas.OrganizationCreation):
    try:
        validate_password(payload.password, payload.confirmed_password, request.user)
        user = User.objects.create_user(
            username=payload.username, password=payload.password
        )
        data = payload.dict(exclude={"username", "password", "confirmed_password"})
        return models.Organization.objects.create(user=user, **data)
    except ValidationError as e:
        raise errors.HttpError(422, f"Password validation failed: {e}")
    except IntegrityError:
        raise errors.HttpError(422, f"Username is already existed: {payload.username}")
    except errors.HttpError as e:
        raise e


@router.post("/register/donator/", auth=None, response=schemas.Donator)
def create_donator(request, payload: schemas.DonatorCreation):
    try:
        validate_password(payload.password, payload.confirmed_password, request.user)
        user = User.objects.create_user(
            username=payload.username, password=payload.password
        )
        data = payload.dict(exclude={"username", "password", "confirmed_password"})
        return models.Donator.objects.create(user=user, **data)
    except ValidationError as e:
        raise errors.HttpError(422, f"Password validation failed: {e}")
    except IntegrityError:
        raise errors.HttpError(422, f"Username is already existed: {payload.username}")
    except errors.HttpError as e:
        raise e


@router.get(
    "/organization-required-items/",
    response=pagination.PaginatedResponseSchema[schemas.RequiredItem],
)
def list_organization_required_items(request, page: int = 1):
    items = models.RequiredItem.objects.filter(organization__user=request.user)
    return pagination.render(
        request, items=items, schema_cls=schemas.RequiredItem, page=page
    )


@router.post("/organization-required-items/", response=schemas.RequiredItem)
def create_organization_required_item(request, payload: schemas.RequiredItemCreation):
    return models.RequiredItem.objects.create(
        organization=request.user.organization, **payload.dict()
    )
