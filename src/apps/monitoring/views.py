import psutil
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.cache import cache
from django.db import connection
from django.conf import settings

logger = logging.getLogger('monitoring')

class IsSuperUser(IsAdminUser):
    """
    Разрешает доступ только суперпользователям
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class SystemHealthView(APIView):
    """
    Проверка состояния системы и сервисов
    """
    permission_classes = [IsSuperUser]

    def get(self, request):
        data = {
            'services': self._check_services(),
            'system': self._get_system_stats()
        }
        return Response(data)

    def _check_services(self):
        services = {}
        
        # PostgreSQL
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                services['postgresql'] = {
                    'status': 'up',
                    'connections': self._get_db_connections()
                }
        except Exception as e:
            services['postgresql'] = {'status': 'down', 'error': str(e)}

        # Redis
        try:
            cache.set('health_check', 'ok', timeout=1)
            cache_value = cache.get('health_check')
            services['redis'] = {
                'status': 'up' if cache_value == 'ok' else 'down',
                'used_memory': self._get_redis_memory()
            }
        except Exception as e:
            services['redis'] = {'status': 'down', 'error': str(e)}

        return services

    def _get_system_stats(self):
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'cores': psutil.cpu_count()
            },
            'memory': {
                'total': self._bytes_to_mb(memory.total),
                'used': self._bytes_to_mb(memory.used),
                'free': self._bytes_to_mb(memory.available),
                'percent': memory.percent
            },
            'disk': {
                'total': self._bytes_to_mb(disk.total),
                'used': self._bytes_to_mb(disk.used),
                'free': self._bytes_to_mb(disk.free),
                'percent': disk.percent
            }
        }

    def _get_db_connections(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT count(*) 
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                return cursor.fetchone()[0]
        except:
            return None

    def _get_redis_memory(self):
        try:
            redis_client = cache.client.get_client()
            info = redis_client.info(section='memory')
            return self._bytes_to_mb(info.get('used_memory', 0))
        except:
            return None

    def _bytes_to_mb(self, bytes_value):
        return round(bytes_value / (1024 * 1024), 2)  # Конвертация в МБ


class ModuleHealthView(APIView):
    """
    Проверка состояния отдельных модулей приложения
    """
    permission_classes = [IsSuperUser]

    def get(self, request):
        modules = {
            'vehicle': self._check_module('apps.vehicle'),
            'trip': self._check_module('apps.trip'),
            'booking': self._check_module('apps.booking'),
            'payment': self._check_module('apps.payment'),
            'seat': self._check_module('apps.seat')
        }
        return Response(modules)

    def _check_module(self, module_path):
        try:
            from importlib import import_module
            import_module(module_path)
            
            if module_path == 'apps.vehicle':
                from apps.vehicle.models import Vehicle
                count = Vehicle.objects.count()
            elif module_path == 'apps.trip':
                from apps.trip.models import Trip
                count = Trip.objects.count()
            elif module_path == 'apps.booking':
                from apps.booking.models import Booking
                count = Booking.objects.count()
            elif module_path == 'apps.payment':
                from apps.payment.models import Payment
                count = Payment.objects.count()
            elif module_path == 'apps.seat':
                from apps.seat.models import Seat
                count = Seat.objects.count()

            return {
                'status': 'up',
                'records': count
            }
        except Exception as e:
            return {
                'status': 'down',
                'error': str(e)
            }