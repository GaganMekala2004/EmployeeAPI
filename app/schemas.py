# Topic: Pydantic Schemas
from pydantic import BaseModel, ConfigDict, constr

# Used when creating a new employee
class EmployeeCreate(BaseModel):

    name: str

    email: str

    department: str

    salary: float

# Used when updating an employee
class EmployeeUpdate(BaseModel):

    name: str | None = None

    email: str | None = None

    department: str | None = None

    salary: float | None = None

# Used when sending employee details back to the client
class EmployeeResponse(BaseModel):

    id: int

    name: str

    email: str

    department: str

    salary: float

    # Read data directly from SQLAlchemy Model
    model_config = ConfigDict(
        from_attributes=True
    )

class UserCreate(BaseModel):
    # Basic email validation without requiring the external email-validator package
    email: constr(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str

class UserLogin(BaseModel):
    # Basic email validation without requiring the external email-validator package
    email: constr(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str

class UserResponse(BaseModel):
    id: int
    # Keep response email validated with same basic pattern
    email: constr(pattern=r'^[^@]+@[^@]+\.[^@]+$')
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str