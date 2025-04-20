from prometheus_client import Counter, Histogram, Gauge, Summary
import time
import psutil

# Счетчик для отслеживания использования шаблонов
TEMPLATE_USAGE_COUNT = Counter(
    'template_usage_total', 
    'Usage count for each template type',
    ['operation_type']
)

# Гистограмма для замера времени генерации PDF
PDF_GENERATION_TIME = Histogram(
    'pdf_generation_duration_seconds', 
    'Time spent generating PDF documents',
    ['operation_type'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 30.0, 60.0)
)

# Метрики использования ресурсов
MEMORY_USAGE = Gauge(
    'pdf_converter_memory_usage_bytes', 
    'Memory usage of the application in bytes'
)

CPU_USAGE = Gauge(
    'pdf_converter_cpu_usage_percent', 
    'CPU usage percentage of the application'
)

# Метрика размера JSON данных
JSON_SIZE = Histogram(
    'json_data_size_bytes',
    'Size of input JSON data in bytes',
    ['operation_type'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
)

class MetricsTimer:
    """Контекстный менеджер для замера времени выполнения операции"""
    
    def __init__(self, metric, labels=None):
        self.metric = metric
        self.labels = labels or {}
        self.start = None
        
    def __enter__(self):
        self.start = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start
        if isinstance(self.metric, Histogram):
            self.metric.labels(**self.labels).observe(duration)
        elif isinstance(self.metric, Summary):
            self.metric.labels(**self.labels).observe(duration)

def update_resource_metrics():
    """Обновляет метрики использования ресурсов"""
    # Обновляем метрику использования памяти
    process = psutil.Process()
    memory_info = process.memory_info()
    MEMORY_USAGE.set(memory_info.rss)  # Resident Set Size
    
    # Обновляем метрику использования CPU
    cpu_percent = process.cpu_percent(interval=0.1)
    CPU_USAGE.set(cpu_percent) 