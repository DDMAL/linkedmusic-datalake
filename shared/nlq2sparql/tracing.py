"""
Enhanced Tracing and Logging for NLQ2SPARQL

This module provides comprehensive tracing capabilities to track:
- Query routing and agent selection
- LLM API calls and responses
- Function calls and their results
- Timing information
- Error handling and retries

Usage:
    from nlq2sparql.tracing import setup_tracing, get_tracer
    
    # Setup tracing with desired level
    setup_tracing(level="DEBUG")
    
    # Get a tracer for your module
    tracer = get_tracer("my_module")
    
    # Trace operations
    with tracer.trace_operation("query_processing"):
        result = process_query(query)
"""

import logging
import time
import json
import uuid
from typing import Dict, Any, Optional, List, ContextManager
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import threading
from dataclasses import dataclass, asdict


@dataclass
class TraceEvent:
    """Individual trace event"""
    event_id: str
    timestamp: str
    level: str
    module: str
    operation: str
    message: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    parent_id: Optional[str] = None


class TraceBuffer:
    """Thread-safe buffer for trace events"""
    
    def __init__(self, max_size: int = 1000):
        self.events: List[TraceEvent] = []
        self.max_size = max_size
        self._lock = threading.Lock()
        
    def add_event(self, event: TraceEvent):
        with self._lock:
            self.events.append(event)
            if len(self.events) > self.max_size:
                self.events.pop(0)  # Remove oldest event
                
    def get_events(self, since: Optional[datetime] = None) -> List[TraceEvent]:
        with self._lock:
            if since is None:
                return self.events.copy()
            
            since_str = since.isoformat()
            return [e for e in self.events if e.timestamp >= since_str]
            
    def clear(self):
        with self._lock:
            self.events.clear()


class Tracer:
    """Individual tracer for a module or component"""
    
    def __init__(self, name: str, buffer: TraceBuffer, logger: logging.Logger):
        self.name = name
        self.buffer = buffer
        self.logger = logger
        self.active_operations: Dict[str, float] = {}
        
    def trace(self, level: str, operation: str, message: str, data: Optional[Dict[str, Any]] = None, parent_id: Optional[str] = None):
        """Add a trace event"""
        event = TraceEvent(
            event_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            module=self.name,
            operation=operation,
            message=message,
            data=data,
            parent_id=parent_id
        )
        
        self.buffer.add_event(event)
        
        # Also log to standard logger
        log_level = getattr(logging, level.upper(), logging.INFO)
        extra_info = f" [{operation}]" if operation else ""
        data_info = f" {json.dumps(data, default=str)}" if data else ""
        self.logger.log(log_level, f"{message}{extra_info}{data_info}")
        
    def info(self, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
        self.trace("INFO", operation, message, data)
        
    def debug(self, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
        self.trace("DEBUG", operation, message, data)
        
    def warning(self, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
        self.trace("WARNING", operation, message, data)
        
    def error(self, operation: str, message: str, data: Optional[Dict[str, Any]] = None):
        self.trace("ERROR", operation, message, data)
        
    @contextmanager
    def trace_operation(self, operation: str, data: Optional[Dict[str, Any]] = None):
        """Context manager to trace an operation with timing"""
        operation_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.trace("INFO", operation, f"Starting operation", {
            "operation_id": operation_id,
            **(data or {})
        })
        
        try:
            yield operation_id
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.trace("ERROR", operation, f"Operation failed: {str(e)}", {
                "operation_id": operation_id,
                "duration_ms": duration,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
        else:
            duration = (time.time() - start_time) * 1000
            self.trace("INFO", operation, f"Operation completed", {
                "operation_id": operation_id,
                "duration_ms": duration
            })
            
    def trace_llm_call(self, provider: str, model: str, messages: List[Dict], response: Any, duration_ms: float):
        """Trace an LLM API call with full details"""
        # Capture full input for detailed logging
        full_input = messages[0].get('content', '') if messages else ''
        
        # Extract response text if available
        response_text = ""
        response_details = {}
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts'):
                    text_parts = []
                    function_calls = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            function_calls.append({
                                "name": func_call.name,
                                "args": dict(func_call.args) if func_call.args else {}
                            })
                    
                    response_text = ''.join(text_parts)
                    response_details = {
                        "text_parts": len(text_parts),
                        "function_calls": function_calls,
                        "has_function_calls": len(function_calls) > 0
                    }
        
        # Log the complete LLM interaction
        self.trace("INFO", "llm_api_call", f"LLM API call to {provider} model {model}", {
            "provider": provider,
            "model": model,
            "input_length": len(full_input),
            "input_text": full_input,
            "output_length": len(response_text),
            "output_text": response_text,
            "duration_ms": duration_ms,
            "response_details": response_details
        })
        
    def trace_function_call(self, function_name: str, arguments: Dict[str, Any], result: Any, duration_ms: float):
        """Trace a function call"""
        self.trace("INFO", "function_call", f"Function call: {function_name}", {
            "function": function_name,
            "arguments": arguments,
            "result": str(result)[:500] if result else None,
            "duration_ms": duration_ms
        })
        
    def trace_agent_routing(self, query: str, selected_agent: str, routing_reason: str):
        """Trace agent selection and routing"""
        self.trace("INFO", "agent_routing", f"Routed to {selected_agent}", {
            "query": query[:200] + "..." if len(query) > 200 else query,
            "selected_agent": selected_agent,
            "routing_reason": routing_reason
        })


class TracingManager:
    """Global tracing manager"""
    
    def __init__(self):
        self.buffer = TraceBuffer()
        self.tracers: Dict[str, Tracer] = {}
        self.enabled = True
        
    def get_tracer(self, name: str) -> Tracer:
        """Get or create a tracer for a module"""
        if name not in self.tracers:
            logger = logging.getLogger(f"nlq2sparql.{name}")
            self.tracers[name] = Tracer(name, self.buffer, logger)
        return self.tracers[name]
        
    def get_trace_summary(self, since: Optional[datetime] = None) -> str:
        """Get a formatted summary of recent trace events"""
        events = self.buffer.get_events(since)
        
        if not events:
            return "No trace events found."
            
        lines = [
            "=" * 80,
            f"TRACE SUMMARY ({len(events)} events)",
            "=" * 80
        ]
        
        current_operation = None
        for event in events:
            time_str = event.timestamp.split('T')[1][:12]  # HH:MM:SS.sss
            
            # Group by operation
            if event.operation != current_operation:
                if current_operation is not None:
                    lines.append("")
                lines.append(f"📍 {event.operation.upper()}")
                lines.append("-" * 40)
                current_operation = event.operation
                
            # Format the event
            level_emoji = {
                "INFO": "ℹ️",
                "DEBUG": "🔍", 
                "WARNING": "⚠️",
                "ERROR": "❌"
            }.get(event.level, "📝")
            
            lines.append(f"{time_str} {level_emoji} [{event.module}] {event.message}")
            
            # Add data if present
            if event.data:
                for key, value in event.data.items():
                    if key in ['duration_ms', 'operation_id']:
                        continue  # Skip these, already shown
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    lines.append(f"    {key}: {value_str}")
                    
            if event.duration_ms:
                lines.append(f"    ⏱️ Duration: {event.duration_ms:.1f}ms")
        
        return "\n".join(lines)
        
    def export_trace_log(self, filename: Optional[str] = None) -> str:
        """Export full trace log to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nlq2sparql_trace_{timestamp}.json"
            
        events_data = [asdict(event) for event in self.buffer.events]
        
        log_data = {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events_data),
            "events": events_data
        }
        
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
            
        return str(output_path)


# Global tracing manager instance
_tracing_manager = TracingManager()


def setup_tracing(level: str = "INFO", enable_file_logging: bool = True) -> TracingManager:
    """
    Setup global tracing configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_file_logging: Whether to enable file logging
        
    Returns:
        The tracing manager instance
    """
    # Configure root logger for nlq2sparql
    logger = logging.getLogger("nlq2sparql")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if enable_file_logging:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(log_dir / f"nlq2sparql_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)  # File gets everything
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return _tracing_manager


def get_tracer(name: str) -> Tracer:
    """Get a tracer for the specified module"""
    return _tracing_manager.get_tracer(name)


def get_trace_summary(since: Optional[datetime] = None) -> str:
    """Get a formatted summary of recent trace events"""
    return _tracing_manager.get_trace_summary(since)


def export_trace_log(filename: Optional[str] = None) -> str:
    """Export full trace log to a file"""
    return _tracing_manager.export_trace_log(filename)


def clear_trace_buffer():
    """Clear the trace buffer"""
    _tracing_manager.buffer.clear()
