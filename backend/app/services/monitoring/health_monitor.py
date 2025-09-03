"""Health monitoring system for AI services."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..common.enhanced_hf_client import enhanced_hf_client
from ..common.fallback_manager import fallback_manager
from ..core.model_manager import model_manager

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    """Overall health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthReport:
    """Comprehensive health report."""
    overall_status: HealthStatus
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    api_endpoints: Dict[str, Dict[str, Any]]
    models: Dict[str, Dict[str, Any]]
    recommendations: List[str]

class HealthMonitor:
    """Monitors health of all AI services and components."""
    
    def __init__(self):
        self.monitoring_interval = 300  # 5 minutes
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_report: Optional[HealthReport] = None
        self.alert_thresholds = {
            "api_success_rate": 0.7,
            "model_load_success": 0.8,
            "response_time": 30.0
        }
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("Health monitoring already running")
            return
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                report = await self.generate_health_report()
                self.last_report = report
                
                # Log critical issues
                if report.overall_status == HealthStatus.CRITICAL:
                    logger.error("CRITICAL: System health is critical")
                    for rec in report.recommendations:
                        logger.error(f"Recommendation: {rec}")
                elif report.overall_status == HealthStatus.DEGRADED:
                    logger.warning("WARNING: System health is degraded")
                
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def generate_health_report(self) -> HealthReport:
        """Generate comprehensive health report."""
        timestamp = datetime.now()
        
        # Check service health
        services_health = await self._check_services_health()
        
        # Check API endpoints health
        api_health = await self._check_api_health()
        
        # Check model health
        models_health = await self._check_models_health()
        
        # Determine overall status
        overall_status = self._determine_overall_status(services_health, api_health, models_health)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(services_health, api_health, models_health)
        
        report = HealthReport(
            overall_status=overall_status,
            timestamp=timestamp,
            services=services_health,
            api_endpoints=api_health,
            models=models_health,
            recommendations=recommendations
        )
        
        return report
    
    async def _check_services_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all AI services."""
        services_health = {}
        
        # Get fallback manager health data
        fallback_health = fallback_manager.get_service_health()
        
        for service_name, health_data in fallback_health.items():
            api_stats = health_data.get("api", {})
            local_stats = health_data.get("local", {})
            
            # Calculate success rates
            api_total = api_stats.get("successes", 0) + api_stats.get("failures", 0)
            local_total = local_stats.get("successes", 0) + local_stats.get("failures", 0)
            
            api_success_rate = api_stats.get("successes", 0) / max(api_total, 1)
            local_success_rate = local_stats.get("successes", 0) / max(local_total, 1)
            
            # Determine service status
            if api_success_rate > 0.8 or local_success_rate > 0.8:
                status = HealthStatus.HEALTHY
            elif api_success_rate > 0.5 or local_success_rate > 0.5:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL
            
            services_health[service_name] = {
                "status": status.value,
                "api_success_rate": api_success_rate,
                "local_success_rate": local_success_rate,
                "api_total_requests": api_total,
                "local_total_requests": local_total,
                "last_api_success": api_stats.get("last_success"),
                "last_local_success": local_stats.get("last_success"),
                "last_api_error": api_stats.get("last_error"),
                "last_local_error": local_stats.get("last_error")
            }
        
        return services_health
    
    async def _check_api_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of HuggingFace API endpoints."""
        api_health = {}
        
        # Get endpoint statistics from enhanced client
        endpoint_stats = enhanced_hf_client.get_endpoint_stats()
        
        for url, stats in endpoint_stats.items():
            # Determine health status
            success_rate = stats.get("success_rate", 0)
            avg_response_time = stats.get("average_response_time", 0)
            consecutive_failures = stats.get("consecutive_failures", 0)
            
            if success_rate > 0.8 and avg_response_time < 10 and consecutive_failures < 3:
                status = HealthStatus.HEALTHY
            elif success_rate > 0.5 and consecutive_failures < 5:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL
            
            api_health[url] = {
                "status": status.value,
                "model_type": stats.get("model_type"),
                "success_rate": success_rate,
                "average_response_time": avg_response_time,
                "consecutive_failures": consecutive_failures,
                "total_requests": stats.get("total_requests", 0),
                "circuit_breaker_state": stats.get("circuit_breaker_state"),
                "last_check": stats.get("last_check")
            }
        
        return api_health
    
    async def _check_models_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of local models."""
        models_health = {}
        
        # Get model information from model manager
        all_models_info = model_manager.get_all_models_info()
        
        for model_type, model_info in all_models_info.items():
            # Determine health status
            is_loaded = model_info.get("is_loaded", False)
            is_healthy = model_info.get("is_healthy", False)
            current_provider = model_info.get("current_provider")
            
            if is_loaded and is_healthy:
                status = HealthStatus.HEALTHY
            elif current_provider or is_loaded:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.CRITICAL
            
            models_health[model_type] = {
                "status": status.value,
                "is_loaded": is_loaded,
                "is_healthy": is_healthy,
                "current_provider": current_provider,
                "hf_model_name": model_info.get("hf_model_name"),
                "local_path": model_info.get("local_path"),
                "device": model_info.get("device")
            }
        
        return models_health
    
    def _determine_overall_status(
        self, 
        services_health: Dict, 
        api_health: Dict, 
        models_health: Dict
    ) -> HealthStatus:
        """Determine overall system health status."""
        all_statuses = []
        
        # Collect all status values
        for health_dict in [services_health, api_health, models_health]:
            for item_health in health_dict.values():
                all_statuses.append(HealthStatus(item_health["status"]))
        
        if not all_statuses:
            return HealthStatus.UNKNOWN
        
        # Determine overall status
        critical_count = sum(1 for s in all_statuses if s == HealthStatus.CRITICAL)
        degraded_count = sum(1 for s in all_statuses if s == HealthStatus.DEGRADED)
        
        if critical_count > len(all_statuses) * 0.3:  # More than 30% critical
            return HealthStatus.CRITICAL
        elif critical_count > 0 or degraded_count > len(all_statuses) * 0.5:  # Any critical or >50% degraded
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _generate_recommendations(
        self, 
        services_health: Dict, 
        api_health: Dict, 
        models_health: Dict
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Check services
        for service_name, health in services_health.items():
            if health["status"] == HealthStatus.CRITICAL.value:
                if health["api_success_rate"] < 0.3 and health["local_success_rate"] < 0.3:
                    recommendations.append(f"Service {service_name} is failing on both API and local - check configuration")
                elif health["api_success_rate"] < 0.3:
                    recommendations.append(f"Service {service_name} API is failing - check API token and endpoints")
                elif health["local_success_rate"] < 0.3:
                    recommendations.append(f"Service {service_name} local model is failing - check model files and dependencies")
        
        # Check API endpoints
        for url, health in api_health.items():
            if health["status"] == HealthStatus.CRITICAL.value:
                if health["consecutive_failures"] > 5:
                    recommendations.append(f"API endpoint {url} has {health['consecutive_failures']} consecutive failures - check endpoint availability")
                if health["success_rate"] < 0.3:
                    recommendations.append(f"API endpoint {url} has low success rate ({health['success_rate']:.2%}) - consider switching to local model")
        
        # Check models
        for model_type, health in models_health.items():
            if health["status"] == HealthStatus.CRITICAL.value:
                if not health["is_loaded"]:
                    recommendations.append(f"Model {model_type} is not loaded - check model files and download")
                if not health["is_healthy"]:
                    recommendations.append(f"Model {model_type} failed health check - verify model integrity")
        
        return recommendations
    
    def get_latest_report(self) -> Optional[HealthReport]:
        """Get the latest health report."""
        return self.last_report
    
    async def force_health_check(self) -> HealthReport:
        """Force immediate health check."""
        return await self.generate_health_report()

# Global health monitor instance
health_monitor = HealthMonitor()
