from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserRead

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def to_user_read(user: User) -> UserRead:
    data = user.model_dump(by_alias=True)
    data["_id"] = str(data["_id"])
    return UserRead.model_validate(data)
