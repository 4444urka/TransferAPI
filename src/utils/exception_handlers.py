from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

def custom_exception_handler(exc, context):
    # Сначала вызываем стандартный обработчик исключений DRF,
    # чтобы получить стандартный ответ (если он есть)
    response = exception_handler(exc, context)

    if isinstance(exc, DjangoValidationError):
        # Если это ValidationError из Django (например, из model.clean())
        if hasattr(exc, 'message_dict'):
            data = exc.message_dict
        elif hasattr(exc, 'messages'):
            data = {'detail': exc.messages}
        else:
            data = {'detail': str(exc)}
        
        # Если стандартный обработчик уже вернул ответ (например, для DRFValidationError),
        # мы можем его обновить или заменить. Но для DjangoValidationError он обычно не вернет.
        # Поэтому создаем новый Response.
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # Если это DRF ValidationError, стандартный обработчик уже должен был его корректно обработать.
    # Если response is None, это означает, что DRF не смог обработать это исключение,
    # и это может быть необработанная ошибка сервера (500).
    # В этом случае мы можем захотеть вернуть JSON вместо HTML, если DEBUG=False.
    if response is None:
        # Проверяем, является ли это необработанным исключением и DEBUG выключен
        # context['view'].settings.DEBUG может быть недоступен, если ошибка произошла до инициализации view.
        # Лучше использовать django.conf.settings.DEBUG
        from django.conf import settings
        if not settings.DEBUG:
            # Для необработанных исключений, которые не являются DjangoValidationError
            # и для которых DRF не предоставил ответа, возвращаем общий JSON 500.
            return Response({'detail': 'Внутренняя ошибка сервера.'}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Если DEBUG=True, позволяем Django отображать стандартную страницу отладки

    return response
