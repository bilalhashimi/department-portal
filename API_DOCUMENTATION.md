# Department Portal API Documentation

## Overview

The Department Portal API is a comprehensive REST API built with Django REST Framework that provides endpoints for managing users, departments, and documents in an organizational setting.

## Base URL
```
http://127.0.0.1:8000/api/v1/
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Authentication Endpoints

#### Login
```http
POST /api/v1/accounts/auth/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "refresh": "refresh_token_here",
    "access": "access_token_here",
    "user": {
        "id": "uuid",
        "username": "username",
        "email": "user@example.com",
        "first_name": "First",
        "last_name": "Last",
        "role": "admin",
        "is_verified": true,
        "is_active": true,
        "full_name": "First Last",
        "profile": null,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
}
```

#### Register
```http
POST /api/v1/accounts/auth/register/
Content-Type: application/json

{
    "email": "newuser@example.com",
    "username": "newuser",
    "first_name": "New",
    "last_name": "User",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

#### Refresh Token
```http
POST /api/v1/accounts/auth/refresh/
Content-Type: application/json

{
    "refresh": "refresh_token_here"
}
```

#### Logout
```http
POST /api/v1/accounts/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "refresh": "refresh_token_here"
}
```

## User Management Endpoints

### User Profile
```http
GET /api/v1/accounts/profile/
Authorization: Bearer <access_token>
```

### Update Profile
```http
PUT /api/v1/accounts/profile/update/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "employee_id": "EMP001",
    "phone_number": "+1234567890",
    "bio": "Employee bio",
    "position": "Software Developer"
}
```

### List Users
```http
GET /api/v1/accounts/users/
Authorization: Bearer <access_token>
```

### User Details
```http
GET /api/v1/accounts/users/{user_id}/
Authorization: Bearer <access_token>
```

### Search Users
```http
GET /api/v1/accounts/users/search/?q=search_term
Authorization: Bearer <access_token>
```

### User Statistics (Admin only)
```http
GET /api/v1/accounts/users/stats/
Authorization: Bearer <access_token>
```

### Change Password
```http
POST /api/v1/accounts/auth/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "current_password": "oldpassword",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
}
```

## Department Management Endpoints

### List Departments
```http
GET /api/v1/departments/
Authorization: Bearer <access_token>
```

### Create Department
```http
POST /api/v1/departments/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Information Technology",
    "code": "IT",
    "description": "Technology department",
    "email": "it@company.com",
    "phone": "+1234567890",
    "location": "Building A, Floor 3"
}
```

### Department Details
```http
GET /api/v1/departments/{department_id}/
Authorization: Bearer <access_token>
```

### Update Department
```http
PUT /api/v1/departments/{department_id}/update/
Authorization: Bearer <access_token>
```

### Department Tree Structure
```http
GET /api/v1/departments/tree/
Authorization: Bearer <access_token>
```

### Department Statistics
```http
GET /api/v1/departments/stats/
Authorization: Bearer <access_token>
```

### Department Employees
```http
GET /api/v1/departments/{department_id}/employees/
Authorization: Bearer <access_token>
```

## Position Management

### List Positions
```http
GET /api/v1/departments/positions/
Authorization: Bearer <access_token>
```

### Create Position
```http
POST /api/v1/departments/positions/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "Senior Developer",
    "department": "department_uuid",
    "description": "Senior software developer position",
    "employment_type": "full_time",
    "level": "senior",
    "min_salary": 80000,
    "max_salary": 120000
}
```

### Position Details
```http
GET /api/v1/departments/positions/{position_id}/
Authorization: Bearer <access_token>
```

## Employee Assignments

### List Assignments
```http
GET /api/v1/departments/assignments/
Authorization: Bearer <access_token>
```

### Create Assignment
```http
POST /api/v1/departments/assignments/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "employee": "employee_uuid",
    "department": "department_uuid",
    "position": "position_uuid",
    "start_date": "2025-01-01",
    "is_primary": true
}
```

### End Assignment
```http
POST /api/v1/departments/assignments/{assignment_id}/end/
Authorization: Bearer <access_token>
```

## Budget Management

### List Budgets
```http
GET /api/v1/departments/budgets/
Authorization: Bearer <access_token>
```

### Create Budget
```http
POST /api/v1/departments/budgets/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "department": "department_uuid",
    "fiscal_year": 2025,
    "budget_type": "operational",
    "allocated_amount": 500000,
    "notes": "Annual operational budget"
}
```

### Approve Budget
```http
POST /api/v1/departments/budgets/{budget_id}/approve/
Authorization: Bearer <access_token>
```

## Document Management Endpoints

### List Documents
```http
GET /api/v1/documents/
Authorization: Bearer <access_token>
```

### Create Document
```http
POST /api/v1/documents/create/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
    "title": "Document Title",
    "description": "Document description",
    "category": "category_uuid",
    "file": <file_upload>,
    "status": "draft",
    "priority": "medium"
}
```

### Document Details
```http
GET /api/v1/documents/{document_id}/
Authorization: Bearer <access_token>
```

### Download Document
```http
GET /api/v1/documents/{document_id}/download/
Authorization: Bearer <access_token>
```

### Document Search
```http
GET /api/v1/documents/search/?q=search_term
Authorization: Bearer <access_token>
```

### Document Statistics
```http
GET /api/v1/documents/stats/
Authorization: Bearer <access_token>
```

## Document Categories

### List Categories
```http
GET /api/v1/documents/categories/
Authorization: Bearer <access_token>
```

### Create Category
```http
POST /api/v1/documents/categories/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Policies",
    "description": "Company policies and procedures",
    "department": "department_uuid",
    "is_public": true,
    "color": "#3B82F6",
    "icon": "folder"
}
```

## Document Tags

### List Tags
```http
GET /api/v1/documents/tags/
Authorization: Bearer <access_token>
```

### Create Tag
```http
POST /api/v1/documents/tags/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Important",
    "color": "#EF4444"
}
```

## Document Workflow

### Submit for Review
```http
POST /api/v1/documents/{document_id}/submit-review/
Authorization: Bearer <access_token>
```

### Approve Document
```http
POST /api/v1/documents/{document_id}/approve/
Authorization: Bearer <access_token>
```

### Publish Document
```http
POST /api/v1/documents/{document_id}/publish/
Authorization: Bearer <access_token>
```

### Archive Document
```http
POST /api/v1/documents/{document_id}/archive/
Authorization: Bearer <access_token>
```

## Document Comments

### List Comments
```http
GET /api/v1/documents/{document_id}/comments/
Authorization: Bearer <access_token>
```

### Create Comment
```http
POST /api/v1/documents/{document_id}/comments/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "content": "This is a comment on the document",
    "parent_comment": null
}
```

### Resolve Comment
```http
POST /api/v1/documents/comments/{comment_id}/resolve/
Authorization: Bearer <access_token>
```

## Document Permissions

### List Permissions
```http
GET /api/v1/documents/{document_id}/permissions/
Authorization: Bearer <access_token>
```

### Grant Permission
```http
POST /api/v1/documents/{document_id}/permissions/create/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "user": "user_uuid",
    "permission": "view",
    "expires_at": "2025-12-31T23:59:59Z"
}
```

## Reports

### Organization Chart
```http
GET /api/v1/departments/reports/org-chart/
Authorization: Bearer <access_token>
```

### Performance Report
```http
GET /api/v1/departments/reports/performance/
Authorization: Bearer <access_token>
```

### Budget Utilization Report
```http
GET /api/v1/departments/reports/budget-utilization/
Authorization: Bearer <access_token>
```

### Document Usage Report
```http
GET /api/v1/documents/reports/usage/
Authorization: Bearer <access_token>
```

### User Activity Report
```http
GET /api/v1/documents/reports/user-activity/
Authorization: Bearer <access_token>
```

## Error Responses

The API returns standard HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error response format:
```json
{
    "error": "Error message",
    "details": "Additional error details"
}
```

## Data Models

### User Roles
- `admin` - Administrator
- `department_head` - Department Head
- `manager` - Manager
- `employee` - Employee
- `intern` - Intern

### Document Status
- `draft` - Draft
- `review` - Under Review
- `approved` - Approved
- `published` - Published
- `archived` - Archived
- `obsolete` - Obsolete

### Document Priority
- `low` - Low
- `medium` - Medium
- `high` - High
- `critical` - Critical

### Employment Types
- `full_time` - Full Time
- `part_time` - Part Time
- `contract` - Contract
- `internship` - Internship
- `temporary` - Temporary

### Position Levels
- `entry` - Entry Level
- `junior` - Junior
- `mid` - Mid Level
- `senior` - Senior
- `lead` - Lead
- `manager` - Manager
- `director` - Director
- `executive` - Executive

## Health Check

```http
GET /health/
```

Returns:
```json
{
    "status": "healthy",
    "message": "Department Portal API is running",
    "version": "1.0.0"
}
``` 