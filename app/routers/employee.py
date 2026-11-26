# ==========================
# Topic: Employee Endpoints
# ==========================

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.dependencies import get_db
from app.models import User
from app.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)
from app.security import (
    get_current_user,
    require_admin
)

# Configure Logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


# ==========================
# Create Employee
# ==========================
@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee(
    employee: EmployeeCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    logger.info("Admin is creating an employee.")

    created_employee = crud.create_employee(
        db,
        employee
    )

    logger.info(
        "Employee created successfully. ID=%s, Email=%s",
        created_employee.id,
        str(created_employee.email).replace("\n", "\\n").replace("\r", "\\r")
    )

    return created_employee


# ==========================
# Get All Employees
# ==========================
@router.get("/", response_model=list[EmployeeResponse])
def get_employees(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 5,
    department: str | None = None,
    search: str | None = None,
):
    logger.info(
        "User '%s' requested employee list (skip=%s, limit=%s, department=%s, search=%s).",
        str(current_user.email).replace("\n", "\\n").replace("\r", "\\r"),
        skip,
        limit,
        str(department).replace("\n", "\\n").replace("\r", "\\r"),
        str(search).replace("\n", "\\n").replace("\r", "\\r")
    )

    employees = crud.get_employees(
        db,
        skip,
        limit,
        department,
        search
    )

    logger.info(
        f"{len(employees)} employee(s) returned."
    )

    return employees


# ==========================
# Get Employee By ID
# ==========================
@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    logger.info(
        "User requested employee ID=%s.",
        employee_id
    )

    employee = crud.get_employee(
        db,
        employee_id
    )

    if employee is None:

        logger.warning(
            "Employee not found."
        )

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    logger.info(
        "Employee retrieved successfully."
    )

    return employee


# ==========================
# Update Employee
# ==========================
@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    logger.info(
        f"Admin is updating employee ID={employee_id}."
    )

    updated_employee = crud.update_employee(
        db,
        employee_id,
        employee
    )

    if updated_employee is None:

        logger.warning(
            "Update failed. Employee not found."
        )

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    logger.info(
        "Employee updated successfully."
    )

    return updated_employee


# ==========================
# Delete Employee
# ==========================
@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    logger.info(
        f"Admin is deleting employee ID={employee_id}."
    )

    employee = crud.delete_employee(
        db,
        employee_id
    )

    if employee is None:

        logger.warning(
            "Delete failed. Employee not found."
        )

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    logger.info(
        "Employee deleted successfully."
    )

    return {
        "message": "Employee deleted successfully"
    }