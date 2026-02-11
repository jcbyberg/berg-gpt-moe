"""Performance metrics tracking."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
import time
import json


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    agent_id: str
    task: str
    duration_ms: float
    success: bool
    error: str = ""
    timestamp: datetime
    tools_called: list[str] = None
    
    def __post_init__(self):
        if self.tools_called is None:
            self.tools_called = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class SystemMetrics:
    """Overall system metrics."""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.memory_usage is None:
            self.memory_usage = {}


class MetricsTracker:
    """Track metrics across the system."""
    
    def __init__(self):
        self._system_metrics = SystemMetrics()
        self._agent_metrics: Dict[str, list[AgentMetrics]] = {}
    
    def record_agent_execution(
        self,
        agent_id: str,
        task: str,
        duration_ms: float,
        success: bool,
        error: str = "",
        tools_called: list[str] = None
    ):
        """Record an agent execution."""
        metrics = AgentMetrics(
            agent_id=agent_id,
            task=task,
            duration_ms=duration_ms,
            success=success,
            error=error,
            tools_called=tools_called
        )
        
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = []
        
        self._agent_metrics[agent_id].append(metrics)
        
        # Update system metrics
        self._system_metrics.total_queries += 1
        if success:
            self._system_metrics.successful_queries += 1
        else:
            self._system_metrics.failed_queries += 1
        
        # Update average response time
        total_duration = sum(m.duration_ms for m in self._agent_metrics.values() for m in m)
        total_count = sum(len(m) for m in self._agent_metrics.values())
        if total_count > 0:
            self._system_metrics.avg_response_time_ms = total_duration / total_count
    
    def get_agent_metrics(self, agent_id: str) -> list[AgentMetrics]:
        """Get metrics for a specific agent."""
        return self._agent_metrics.get(agent_id, [])
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get overall system metrics."""
        return self._system_metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "system": {
                "total_queries": self._system_metrics.total_queries,
                "successful_queries": self._system_metrics.successful_queries,
                "failed_queries": self._system_metrics.failed_queries,
                "avg_response_time_ms": self._system_metrics.avg_response_time_ms,
                "memory_usage": self._system_metrics.memory_usage,
            },
            "agents": {
                agent_id: [
                    {
                        "agent_id": m.agent_id,
                        "task": m.task,
                        "duration_ms": m.duration_ms,
                        "success": m.success,
                        "error": m.error,
                        "timestamp": m.timestamp.isoformat(),
                        "tools_called": m.tools_called,
                    }
                    for m in metrics
                ]
                for agent_id, metrics in self._agent_metrics.items()
            },
        }
    
    def to_json(self) -> str:
        """Convert metrics to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
