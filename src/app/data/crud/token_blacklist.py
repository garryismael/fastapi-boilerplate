from app.data.model.token_blacklist import TokenBlacklistModel
from app.domain.token_blacklist.models import (
    TokenBlacklistCreate,
    TokenBlacklistUpdate,
    TokenDelete,
)
from fastcrud import FastCRUD

CRUDTokenBlacklist = FastCRUD[
    TokenBlacklistModel,
    TokenBlacklistCreate,
    TokenBlacklistUpdate,
    TokenBlacklistUpdate,
    TokenDelete,
]
crud_token_blacklist = CRUDTokenBlacklist(TokenBlacklistModel)
