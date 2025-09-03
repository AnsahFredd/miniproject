# app/core/celery_signals.py
import logging
import asyncio
import gc

logger = logging.getLogger(__name__)


def worker_process_init_handler(sender=None, conf=None, **kwargs):
    """Initialize worker process"""
    logger.info("Worker process initializing...")
    
    # Set up fresh logging for this worker
    logging.basicConfig(level=logging.INFO)
    
    # Any other per-process initialization can go here
    logger.info("Worker process initialized successfully")


def worker_shutdown_handler(sender=None, **kwargs):
    """Clean up when worker shuts down"""
    logger.info("Worker shutting down, cleaning up...")
    
    try:
        # Close any remaining event loops
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                loop.close()
        except:
            pass
            
        logger.info("Worker shutdown cleanup completed")
    except Exception as e:
        logger.error(f"Error during worker shutdown: {e}")


def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Run before each task"""
    logger.debug(f"Task {task_id} starting: {task.name}")


def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Run after each task"""
    logger.debug(f"Task {task_id} completed: {task.name} (state: {state})")
    
    # Force garbage collection after each task to prevent memory leaks
    gc.collect()


def setup_celery_signals():
    """Setup Celery signals - call this from worker startup"""
    try:
        from celery.signals import worker_process_init, worker_shutdown, task_prerun, task_postrun
        
        worker_process_init.connect(worker_process_init_handler)
        worker_shutdown.connect(worker_shutdown_handler)
        task_prerun.connect(task_prerun_handler)
        task_postrun.connect(task_postrun_handler)
        
        logger.info("Celery signals registered successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to register Celery signals: {e}")
        return False