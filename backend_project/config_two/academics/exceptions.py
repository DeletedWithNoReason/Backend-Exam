from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "status": "error",
                "message": "Error 403: You don't have access to this page."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    return response