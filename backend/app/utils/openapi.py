"""Shared OpenAPI error examples used across route decorators."""

ERROR_400 = {
    "description": "Bad Request - Invalid input",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input",
                    "details": {},
                }
            }
        }
    },
}

ERROR_401 = {
    "description": "Unauthorized - Missing or invalid JWT token",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Could not validate credentials",
                    "details": {},
                }
            }
        }
    },
}

ERROR_404 = {
    "description": "Not Found - Resource doesn't exist or access denied",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found",
                    "details": {},
                }
            }
        }
    },
}

ERROR_422 = {
    "description": "Validation Error",
    "content": {
        "application/json": {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "pattern"],
                        "msg": "ensure this value is greater than or equal to 1",
                        "type": "value_error",
                        "input": 0,
                    }
                ]
            }
        }
    },
}

ERROR_429 = {
    "description": "Rate limit exceeded",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded",
                    "details": {},
                }
            }
        }
    },
}

ERROR_500 = {
    "description": "Internal Server Error",
    "content": {
        "application/json": {
            "example": {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            }
        }
    },
}