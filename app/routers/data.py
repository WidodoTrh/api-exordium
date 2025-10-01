from fastapi import APIRouter, Depends
from app.core.secure import get_current_user_from_cookie
from app.models.user import User

router = APIRouter()

@router.get("/data")
def protected_data(curr_usr: User = Depends(get_current_user_from_cookie)):
    return {
        "msg": "rahasia banget ",
        "user": curr_usr.email
    }
