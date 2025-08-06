from app.models.user import User

async def get_user_by_email(email: str) -> User | None:
    return await User.find_one(User.email == email)

async def update_user_password(user: User, hashed_password: str) -> User:
    user.hashed_password = hashed_password
    await user.save()
    return user  #reteun