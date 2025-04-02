from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.db.database import get_db
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.reservation import Reservation
from app.core.security import SECRET_KEY, ALGORITHM

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_current_user_from_session(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.session.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


# --- GET endpoints for login and register pages ---

@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# --- Dashboard and Profile Endpoints ---

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    if user.role == "host":
        restaurants = db.query(Restaurant).filter(Restaurant.owner_id == user.id).all()
        reservations = []
        for r in restaurants:
            res_list = db.query(Reservation).filter(Reservation.restaurant_id == r.id).all()
            for res in res_list:
                client = db.query(User).filter(User.id == res.client_id).first()
                reservations.append({"reservation": res, "restaurant": r, "client": client})
        return templates.TemplateResponse("dashboard_host.html",
                                          {"request": request, "user": user, "restaurants": restaurants,
                                           "reservations": reservations})
    else:
        restaurants = db.query(Restaurant).all()
        reservations = db.query(Reservation).filter(Reservation.client_id == user.id).all()
        return templates.TemplateResponse("dashboard_client.html",
                                          {"request": request, "user": user, "restaurants": restaurants,
                                           "reservations": reservations})


# --- Restaurant Detail Endpoint (renamed to avoid conflict) ---

@router.get("/restaurant/detail/{restaurant_id}", response_class=HTMLResponse)
def restaurant_detail(request: Request, restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return templates.TemplateResponse("restaurant_detail.html", {"request": request, "restaurant": restaurant})


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


# --- Endpoints for hosts to add/edit restaurants ---

@router.get("/restaurant/add_form", response_class=HTMLResponse)
def add_restaurant_form_view(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    if user.role != "host":
        raise HTTPException(status_code=403, detail="Only hosts can add restaurants.")
    return templates.TemplateResponse("add_restaurant_form.html", {"request": request})


@router.post("/restaurant/add_form")
def add_restaurant_view(
        request: Request,
        name: str = Form(...),
        num_tables: int = Form(...),
        table_capacity: int = Form(...),
        working_time: str = Form(...),
        db: Session = Depends(get_db)
):
    user = get_current_user_from_session(request, db)
    if user.role != "host":
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
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/restaurant/edit/{restaurant_id}", response_class=HTMLResponse)
def edit_restaurant_form(request: Request, restaurant_id: int, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.owner_id == user.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found or not owned by you")
    return templates.TemplateResponse("edit_restaurant.html", {"request": request, "restaurant": restaurant})


@router.post("/restaurant/edit/{restaurant_id}")
def edit_restaurant(
        request: Request,
        restaurant_id: int,
        name: str = Form(...),
        num_tables: int = Form(...),
        table_capacity: int = Form(...),
        working_time: str = Form(...),
        db: Session = Depends(get_db)
):
    user = get_current_user_from_session(request, db)
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.owner_id == user.id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found or not owned by you")
    restaurant.name = name
    restaurant.num_tables = num_tables
    restaurant.table_capacity = table_capacity
    restaurant.working_time = working_time
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)


# --- Reservation Endpoints ---

# GET: Show a reservation booking form for a specific restaurant (clients only)
@router.get("/reservation/book/{restaurant_id}", response_class=HTMLResponse)
def reservation_form(request: Request, restaurant_id: int, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Only clients can book reservations.")
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    # Provide a list of table numbers (1 to num_tables) for selection.
    table_numbers = list(range(1, restaurant.num_tables + 1))
    return templates.TemplateResponse("reservation_form.html",
                                      {"request": request, "restaurant": restaurant, "table_numbers": table_numbers,
                                       "error": ""})


# POST: Process a reservation booking request with table selection and time limit
@router.post("/reservation/book/{restaurant_id}")
def book_reservation(
        request: Request,
        restaurant_id: int,
        table_number: int = Form(...),
        start_time: str = Form(...),  # Expecting ISO format: "YYYY-MM-DDTHH:MM"
        end_time: str = Form(...),
        db: Session = Depends(get_db)
):
    user = get_current_user_from_session(request, db)
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Only clients can book reservations.")
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Validate table number is within restaurant range
    if not (1 <= table_number <= restaurant.num_tables):
        raise HTTPException(status_code=400, detail="Invalid table number for this restaurant.")

    try:
        new_start = datetime.fromisoformat(start_time)
        new_end = datetime.fromisoformat(end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM).")

    if new_start >= new_end:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")

    now = datetime.now()
    # Ensure reservation is not in the past
    if new_start < now:
        raise HTTPException(status_code=400, detail="Reservation time cannot be in the past.")
    # Limit booking to today, tomorrow, and the day after tomorrow (2 days ahead)
    if new_start > now + timedelta(days=2):
        raise HTTPException(status_code=400, detail="You can only book reservations up to two days ahead.")

    # Check if the reservation falls within restaurant working hours
    try:
        work_start_str, work_end_str = restaurant.working_time.split("-")
        work_start = datetime.strptime(work_start_str.strip(), "%H:%M").time()
        work_end = datetime.strptime(work_end_str.strip(), "%H:%M").time()
    except Exception:
        raise HTTPException(status_code=500, detail="Invalid restaurant working time format.")

    if not (work_start <= new_start.time() <= work_end and work_start <= new_end.time() <= work_end):
        raise HTTPException(status_code=400, detail="Reservation time must be within restaurant working hours.")

    # Check if the specific table is available for the desired time slot.
    overlapping = db.query(Reservation).filter(
        Reservation.restaurant_id == restaurant_id,
        Reservation.table_number == table_number,
        Reservation.start_time < new_end,
        Reservation.end_time > new_start
    ).count()

    if overlapping > 0:
        # Return JSON response indicating the table is booked
        return JSONResponse(status_code=400,
                            content={"error": f"Table {table_number} is already booked for the selected time slot."})

    # Create the reservation
    reservation = Reservation(
        restaurant_id=restaurant_id,
        client_id=user.id,
        table_number=table_number,
        start_time=new_start,
        end_time=new_end
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return RedirectResponse(url="/reservations", status_code=302)


# GET: View reservations (clients see their own; hosts see reservations for their restaurants)
@router.get("/reservations", response_class=HTMLResponse)
def view_reservations(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    if user.role == "client":
        reservations = db.query(Reservation).filter(Reservation.client_id == user.id).all()
        return templates.TemplateResponse("my_reservations.html",
                                          {"request": request, "user": user, "reservations": reservations})
    elif user.role == "host":
        restaurants = db.query(Restaurant).filter(Restaurant.owner_id == user.id).all()
        reservations = []
        for r in restaurants:
            res_list = db.query(Reservation).filter(Reservation.restaurant_id == r.id).all()
            for res in res_list:
                client = db.query(User).filter(User.id == res.client_id).first()
                reservations.append({"reservation": res, "restaurant": r, "client": client})
        return templates.TemplateResponse("host_reservations.html",
                                          {"request": request, "user": user, "reservations": reservations})
    else:
        raise HTTPException(status_code=400, detail="Invalid role.")


# POST: Cancel a reservation (clients only)
@router.post("/reservation/cancel/{reservation_id}")
def cancel_reservation(request: Request, reservation_id: int, db: Session = Depends(get_db)):
    user = get_current_user_from_session(request, db)
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id,
                                               Reservation.client_id == user.id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found or not owned by you")
    db.delete(reservation)
    db.commit()
    return RedirectResponse(url="/reservations", status_code=302)
