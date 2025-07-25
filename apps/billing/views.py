from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def billing_status(request):
    return Response({"status": "billing service ready"})