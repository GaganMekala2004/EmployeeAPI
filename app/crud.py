# ==========================
# Topic: CRUD Operations
# ==========================

import logging

from sqlalchemy.orm import Session

from app import models, schemas

logger = logging.getLogger(__name__)


# ==========================
# Employee CRUD
# ==========================

def create_employee(
    db: Session,
    employee: schemas.EmployeeCreate
):
    db_employee = models.Employee(
        **employee.model_dump()
    )

    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    logger.info(
        f"Employee created: {db_employee.email}"
    )

    return db_employee


def get_employees(
    db: Session,
    skip: int = 0,
    limit: int = 5,
    department: str | None = None,
    search: str | None = None
):
    query = db.query(models.Employee)

    if department:
        query = query.filter(
            models.Employee.department == department
        )

    if search:
        query = query.filter(
            models.Employee.name.ilike(f"%{search}%")
        )

    employees = query.offset(skip).limit(limit).all()

    logger.info("Fetched employee list.")

    return employees


def get_employee(
    db: Session,
    employee_id: int
):
    employee = db.query(models.Employee).filter(
        models.Employee.id == employee_id
    ).first()

    logger.info(
        f"Fetched employee: {employee_id}"
    )

    return employee


def update_employee(
    db: Session,
    employee_id: int,
    employee: schemas.EmployeeUpdate
):
    db_employee = db.query(models.Employee).filter(
        models.Employee.id == employee_id
    ).first()

    if not db_employee:
        logger.warning(
            f"Employee not found for update: {employee_id}"
        )
        return None

    update_data = employee.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(db_employee, key, value)

    db.commit()
    db.refresh(db_employee)

    logger.info(
        f"Employee updated: {employee_id}"
    )

    return db_employee


def delete_employee(
    db: Session,
    employee_id: int
):
    db_employee = db.query(models.Employee).filter(
        models.Employee.id == employee_id
    ).first()

    if not db_employee:
        logger.warning(
            f"Employee not found for deletion: {employee_id}"
        )
        return None

    db.delete(db_employee)
    db.commit()

    logger.info(
        f"Employee deleted: {employee_id}"
    )

    return db_employee


# ==========================
# User CRUD
# ==========================

def get_user_by_email(
    db: Session,
    email: str
):
    logger.info(
        f"Searching user by email: {email}"
    )

    return db.query(models.User).filter(
        models.User.email == email
    ).first()


def create_user(
    db: Session,
    user: schemas.UserCreate,
    hashed_password: str
):
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info(
        f"User created: {db_user.email}"
    )

    return db_user