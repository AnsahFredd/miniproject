# app/core/celery_app.py - FIXED VERSION
import logging
import platform
import ssl
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

def prepare_redis_url(base_url: str) -> str:
    """Prepare Redis URL with proper SSL configuration and database index."""
    url = base_url.strip()
    
    # Ensure database index is present
    if not any(url.endswith(f'/{i}') for i in range(10)):
        if not url.endswith('/'):
            url += '/0'
        else:
            url += '0'
    
    # Add SSL parameter for secure Redis connections
    if url.startswith("rediss://"):
        if "ssl_cert_reqs" not in url:
            # Add SSL parameter to URL
            separator = "?" if "?" not in url else "&"
            url += f"{separator}ssl_cert_reqs=CERT_NONE"
    
    return url

# Create Celery instance
celery_app = Celery("legal_ai_worker")

# Prepare Redis URLs with proper SSL configuration
redis_broker_url = prepare_redis_url(settings.REDIS_URL)
redis_backend_url = prepare_redis_url(settings.REDIS_URL)

logger.info(f"Using Redis broker URL: {redis_broker_url}")
logger.info(f"Using Redis backend URL: {redis_backend_url}")

# Platform-aware socket options
socket_opts = None
if platform.system() != "Windows":
    socket_opts = {
        'TCP_KEEPINTVL': 1,
        'TCP_KEEPCNT': 3,
        'TCP_KEEPIDLE': 1,
    }

# Common broker options (without URL-level SSL since it's in the URL)
broker_opts = {
    'socket_keepalive': True,
    'socket_connect_timeout': 30,
    'socket_timeout': 30,
    'retry_on_timeout': True,
    'health_check_interval': 10,
    'max_connections': 20,
    'connection_pool_kwargs': {
        'max_connections': 20,
        'retry_on_timeout': True,
    }
}

# Only add socket options for non-Windows platforms
if socket_opts:
    broker_opts['socket_keepalive_options'] = socket_opts

# Backend options (similar to broker)
backend_opts = {
    'socket_keepalive': True,
    'socket_connect_timeout': 30,
    'socket_timeout': 30,
    'retry_on_timeout': True,
    'health_check_interval': 10,
    'max_connections': 10,
    'connection_pool_kwargs': {
        'max_connections': 10,
        'retry_on_timeout': True,
    }
}

if socket_opts:
    backend_opts['socket_keepalive_options'] = socket_opts

# Celery configuration
celery_app.conf.update(
    # Use prepared URLs with SSL parameters
    broker_url=redis_broker_url,
    result_backend=redis_backend_url,

    # Connection retry settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,

    # Worker settings
    worker_cancel_long_running_tasks_on_connection_loss=True,

    # Pool and retry settings
    broker_pool_limit=20,
    result_backend_connection_retry=True,
    result_backend_connection_retry_on_startup=True,

    # Transport options
    broker_transport_options=broker_opts,
    result_backend_transport_options=backend_opts,

    # Task timeouts and behavior
    task_soft_time_limit=600,   # 10 min
    task_time_limit=900,        # 15 min
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Task handling
    task_reject_on_worker_lost=True,
    task_ignore_result=False,

    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Result expiry
    result_expires=3600,  # 1 hour

    # Queue routing
    task_default_queue='lawlens',
    task_routes={
        'app.tasks.document_tasks.process_document_async': {'queue': 'lawlens_ai_processing'},
        'app.tasks.document_tasks.debug_simple_task': {'queue': 'lawlens_ai_processing'},
        'app.tasks.document_tasks.debug_model_loading': {'queue': 'lawlens_ai_processing'},
        'app.tasks.document_tasks.debug_event_loop': {'queue': 'lawlens_ai_processing'},
    },

    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,

    # Worker performance
    worker_disable_rate_limits=True,
    worker_max_tasks_per_child=10,
    worker_max_memory_per_child=200000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

try:
    from app.tasks import document_tasks
    logger.info("Document tasks imported successfully")
except ImportError as e:
    logger.error(f"Failed to import document tasks: {e}")

@celery_app.task
def health_check():
    """Health check task"""
    import asyncio, time
    start_time = time.time()
    test_result = {
        "status": "healthy",
        "timestamp": start_time,
        "redis_connection": "ok",
        "event_loop_test": "pending"
    }
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def test_async():
            await asyncio.sleep(0.01)
            return "ok"
        result = loop.run_until_complete(test_async())
        loop.close()
        test_result["event_loop_test"] = result
    except Exception as e:
        test_result["event_loop_test"] = f"failed: {str(e)}"
        test_result["status"] = "unhealthy"
    test_result["response_time_ms"] = (time.time() - start_time) * 1000
    return test_result