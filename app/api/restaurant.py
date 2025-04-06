from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.schemas.restaurant import RestaurantResponse
from app.models.restaurant import Restaurant
from app.db.database import get_db
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/restaurant",
    tags=["restaurant"]
)


@router.post("/add", response_model=RestaurantResponse)
def add_restaurant(
        name: str = Form(...),
        num_tables: int = Form(...),
        table_capacity: int = Form(...),
        working_time: str = Form(...),
        token: str = Form(...),
        db: Session = Depends(get_db)
):
    # Decode the token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user: User = db.query(User).filter(User.email == email).first()
    if not user or user.role != "host":
        raise HTTPException(status_code=403, detail="Only hosts can add restaurants.")

    restaurant = Restaurant(
        owner_id=user.id,
        name=name,
        num_tables=num_tables,
        table_capacity=table_capacity,
        working_time=working_time
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant
