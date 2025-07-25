@echo off
echo Testing Coworking Platform...

echo Checking container status:
docker-compose ps

echo.
echo Checking web service logs:
docker-compose logs web --tail=20

echo.
echo Testing health endpoint:
curl -s http://localhost:8000/health/ || echo "Health check failed"

pause