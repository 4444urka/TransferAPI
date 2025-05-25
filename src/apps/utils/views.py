from django.http import JsonResponse
from django.db import connection
from django_redis import get_redis_connection

def health_check(request):
    """
    Эндпоинт для проверки работоспособности системы.
    Проверяет соединение с базой данных и Redis.
    """
    health_status = {
        'status': 'ok',
        'database': False,
        'redis': False,
        'components': []
    }
    
    # Проверка базы данных
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['database'] = True
            health_status['components'].append('database')
    except Exception:
        health_status['status'] = 'error'
    
    # Проверка Redis
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        health_status['redis'] = True
        health_status['components'].append('redis')
    except Exception:
        health_status['status'] = 'error'
    
    status_code = 200 if health_status['status'] == 'ok' else 503
    
    return JsonResponse(health_status, status=status_code) 