from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def reviews_status(request):
    return Response({"status": "reviews service ready"})