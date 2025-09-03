# monitor.py - Real-time monitoring for Redis Cloud and Celery tasks
import os
import time
import json
import redis
from datetime import datetime
from celery import Celery
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CeleryMonitor:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        if not self.redis_url:
            raise ValueError("REDIS_URL not set")
        
        # Initialize Redis client
        self.redis_client = redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_timeout=10,
            socket_connect_timeout=10
        )
        
        # Initialize Celery app
        self.celery_app = Celery('monitor')
        self.celery_app.conf.broker_url = self.redis_url
        self.celery_app.conf.result_backend = self.redis_url
    
    def get_worker_status(self):
        """Get status of all Celery workers"""
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = inspect.stats()
            active = inspect.active()
            reserved = inspect.reserved()
            
            if not stats:
                return {"status": "no_workers", "workers": []}
            
            worker_info = []
            for worker_name in stats.keys():
                worker_stats = stats[worker_name]
                worker_active = active.get(worker_name, []) if active else []
                worker_reserved = reserved.get(worker_name, []) if reserved else []
                
                worker_info.append({
                    "name": worker_name,
                    "status": "online",
                    "active_tasks": len(worker_active),
                    "reserved_tasks": len(worker_reserved),
                    "total_tasks": worker_stats.get('total', 0),
                    "pool": worker_stats.get('pool', {}),
                    "active_task_details": worker_active[:3]  # Show first 3 active tasks
                })
            
            return {"status": "online", "workers": worker_info}
            
        except Exception as e:
            logger.error(f"Failed to get worker status: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_redis_info(self):
        """Get Redis Cloud information"""
        try:
            info = self.redis_client.info()
            memory_info = self.redis_client.info('memory')
            
            return {
                "connection": "ok",
                "version": info.get('redis_version', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": memory_info.get('used_memory_human', 'N/A'),
                "max_memory": memory_info.get('maxmemory_human', 'N/A'),
                "memory_usage_percent": round(
                    (memory_info.get('used_memory', 0) / memory_info.get('maxmemory', 1)) * 100, 2
                ) if memory_info.get('maxmemory', 0) > 0 else 0,
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "uptime_in_seconds": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {"connection": "failed", "error": str(e)}
    
    def get_task_queue_info(self):
        """Get information about task queues"""
        try:
            # Get queue lengths
            ai_processing_length = self.redis_client.llen('ai_processing')
            default_length = self.redis_client.llen('default')
            
            # Get recent task results (last 10)
            recent_tasks = []
            for key in self.redis_client.scan_iter(match="celery-task-meta-*", count=10):
                try:
                    task_data = self.redis_client.get(key)
                    if task_data:
                        task_info = json.loads(task_data)
                        task_id = key.replace('celery-task-meta-', '')
                        recent_tasks.append({
                            "task_id": task_id,
                            "status": task_info.get("status", "unknown"),
                            "result": task_info.get("result", {}),
                            "traceback": task_info.get("traceback", None)
                        })
                except Exception:
                    continue
            
            return {
                "ai_processing_queue": ai_processing_length,
                "default_queue": default_length,
                "recent_tasks": recent_tasks[:10]  # Limit to 10 most recent
            }
        except Exception as e:
            return {"error": str(e)}
    
    def monitor_document_task(self, task_id, timeout=600):
        """Monitor a specific document processing task"""
        start_time = time.time()
        
        print(f"\nMonitoring task: {task_id}")
        print("=" * 50)
        
        while time.time() - start_time < timeout:
            try:
                # Get task result
                result = self.celery_app.AsyncResult(task_id)
                
                print(f"\nTime: {datetime.now().strftime('%H:%M:%S')}")
                print(f"Task State: {result.state}")
                
                if result.state == 'PENDING':
                    print("Status: Task not yet started or unknown")
                
                elif result.state == 'PROGRESS':
                    info = result.info
                    stage = info.get('stage', 'unknown')
                    progress = info.get('progress', 0)
                    message = info.get('message', 'Processing...')
                    
                    print(f"Stage: {stage}")
                    print(f"Progress: {progress}%")
                    print(f"Message: {message}")
                    
                    # Show progress bar
                    bar_length = 30
                    filled_length = int(bar_length * progress // 100)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    print(f"Progress: |{bar}| {progress}%")
                
                elif result.state == 'SUCCESS':
                    print("Status: COMPLETED SUCCESSFULLY!")
                    result_data = result.result
                    if isinstance(result_data, dict):
                        print(f"Processing time: {result_data.get('processing_time_seconds', 'N/A')}s")
                        print(f"Document type: {result_data.get('classification', {}).get('document_type', 'N/A')}")
                        print(f"Summary length: {result_data.get('summary_length', 'N/A')} chars")
                        print(f"AI tags: {len(result_data.get('ai_tags', []))}")
                    break
                
                elif result.state == 'FAILURE':
                    print("Status: FAILED!")
                    print(f"Error: {result.info}")
                    break
                
                else:
                    print(f"Status: {result.state}")
                    if result.info:
                        print(f"Info: {result.info}")
                
                # Wait before next check
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user")
                break
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)
        
        print("\nMonitoring completed")
    
    def show_dashboard(self):
        """Show real-time dashboard"""
        print("CELERY & REDIS CLOUD DASHBOARD")
        print("=" * 50)
        
        try:
            while True:
                # Clear screen (works on most terminals)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("CELERY & REDIS CLOUD DASHBOARD")
                print("=" * 50)
                print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                # Redis status
                redis_info = self.get_redis_info()
                print("REDIS CLOUD STATUS:")
                if redis_info["connection"] == "ok":
                    print(f"  Connection: ✅ Online")
                    print(f"  Memory Usage: {redis_info['used_memory']} / {redis_info['max_memory']} ({redis_info['memory_usage_percent']}%)")
                    print(f"  Connected Clients: {redis_info['connected_clients']}")
                    print(f"  Uptime: {redis_info['uptime_in_seconds']}s")
                else:
                    print(f"  Connection: ❌ Failed - {redis_info.get('error', 'Unknown error')}")
                
                print()
                
                # Worker status
                worker_status = self.get_worker_status()
                print("CELERY WORKERS:")
                if worker_status["status"] == "online":
                    for worker in worker_status["workers"]:
                        print(f"  {worker['name']}: ✅ Online")
                        print(f"    Active Tasks: {worker['active_tasks']}")
                        print(f"    Reserved Tasks: {worker['reserved_tasks']}")
                        print(f"    Total Completed: {worker['total_tasks']}")
                        if worker['active_task_details']:
                            print(f"    Current: {worker['active_task_details'][0].get('name', 'unknown')}")
                elif worker_status["status"] == "no_workers":
                    print("  ❌ No workers online")
                else:
                    print(f"  ❌ Error: {worker_status.get('error', 'Unknown')}")
                
                print()
                
                # Queue status
                queue_info = self.get_task_queue_info()
                if "error" not in queue_info:
                    print("TASK QUEUES:")
                    print(f"  AI Processing Queue: {queue_info['ai_processing_queue']} tasks")
                    print(f"  Default Queue: {queue_info['default_queue']} tasks")
                    
                    if queue_info['recent_tasks']:
                        print("\n  RECENT TASKS:")
                        for task in queue_info['recent_tasks'][:5]:
                            status_emoji = "✅" if task['status'] == 'SUCCESS' else "❌" if task['status'] == 'FAILURE' else "⏳"
                            print(f"    {task['task_id'][:8]}... : {status_emoji} {task['status']}")
                
                print("\n" + "=" * 50)
                print("Press Ctrl+C to exit dashboard")
                
                # Wait 10 seconds before refresh
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\nDashboard closed")

def main():
    """Main function to run monitoring commands"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python monitor.py dashboard           - Show real-time dashboard")
        print("  python monitor.py status             - Show current status")
        print("  python monitor.py task <task_id>     - Monitor specific task")
        return
    
    monitor = CeleryMonitor()
    command = sys.argv[1]
    
    if command == "dashboard":
        monitor.show_dashboard()
    
    elif command == "status":
        print("CURRENT STATUS")
        print("=" * 30)
        
        redis_info = monitor.get_redis_info()
        print("Redis:", "✅ Connected" if redis_info["connection"] == "ok" else f"❌ {redis_info.get('error')}")
        
        worker_status = monitor.get_worker_status()
        worker_count = len(worker_status.get("workers", []))
        print(f"Workers: {worker_count} online")
        
        queue_info = monitor.get_task_queue_info()
        if "error" not in queue_info:
            total_queued = queue_info["ai_processing_queue"] + queue_info["default_queue"]
            print(f"Queued Tasks: {total_queued}")
    
    elif command == "task" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        monitor.monitor_document_task(task_id)
    
    else:
        print("Unknown command. Use 'dashboard', 'status', or 'task <task_id>'")

if __name__ == "__main__":
    main()