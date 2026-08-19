from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc,context):
    response = drf_exception_handler(
        exc,
        context,
    )

    if response is None:
        return None

    original_data = response.data

    if isinstance(exc, APIException):
        codes = exc.get_codes()
    else:
        codes = "error"

    if (
        isinstance(original_data, dict)
        and "detail" in original_data
    ):
        message = str(
            original_data["detail"]
        )

        code = (
            codes
            if isinstance(codes, str)
            else "error"
        )

        details = {}

    else:
        message = "Request validation failed."
        code = "validation_error"
        details = original_data

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }

    return response