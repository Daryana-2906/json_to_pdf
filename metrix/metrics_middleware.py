from flask import request, Flask
import time
from prometheus_client import start_http_server
from metrix.prometheus_metrics import update_resource_metrics

class PrometheusMiddleware:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        request.start_time = time.time()
        # Обновляем метрики ресурсов при поступлении запроса
        update_resource_metrics()

    def after_request(self, response):
        # Обновляем метрики ресурсов после обработки запроса
        update_resource_metrics()
        return response

def setup_metrics(app: Flask, port=8000):
    """
    Настраивает Prometheus метрики для Flask приложения
    
    :param app: Flask приложение
    :param port: Порт для эндпоинта Prometheus метрик
    """
    # Запускаем HTTP сервер для метрик Prometheus
    start_http_server(port)
    
    # Регистрируем middleware
    PrometheusMiddleware(app) 