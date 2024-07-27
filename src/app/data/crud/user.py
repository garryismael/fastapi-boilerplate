from app.data.model.user import UserModel
from app.domain.user.models import (
    UserCreateInternal,
    UserDelete,
    UserUpdate,
    UserUpdateInternal,
)
from fastcrud import FastCRUD

CRUDUser = FastCRUD[
    UserModel,
    UserCreateInternal,
    UserUpdate,
    UserUpdateInternal,
    UserDelete,
]
crud_users = CRUDUser(UserModel)
