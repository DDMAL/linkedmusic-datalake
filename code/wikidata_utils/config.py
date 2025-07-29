"""
Configuration module for the FederatedQueryOptimizer.

This module provides configuration settings and presets for different
optimization scenarios and use cases.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class OptimizationConfig:
    """Configuration settings for query optimization."""
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: float = 3600.0  # 1 hour
    max_cache_entries: int = 1000
    
    # Query rewriting settings
    add_timeout_hint: bool = True
    default_timeout: int = 120000  # 120 seconds in milliseconds
    add_query_hints: bool = True
    move_filters_to_service: bool = True
    add_runtime_optimizer: bool = True
    max_parallel_requests: int = 1
    
    # Performance settings
    enable_batching: bool = True
    batch_size: int = 100
    enable_early_termination: bool = True
    
    # Logging settings
    log_optimizations: bool = True
    log_cache_operations: bool = False
    log_performance_stats: bool = True


# Predefined configurations for different use cases

DIAMM_CONFIG = OptimizationConfig(
    cache_enabled=True,
    cache_ttl=1800.0,  # 30 minutes - DIAMM data changes occasionally
    add_timeout_hint=True,
    default_timeout=180000,  # 3 minutes for complex DIAMM queries
    add_query_hints=True,
    move_filters_to_service=True,
    max_parallel_requests=1,  # Conservative for Wikidata
    log_optimizations=True
)

RESEARCH_CONFIG = OptimizationConfig(
    cache_enabled=True,
    cache_ttl=7200.0,  # 2 hours - research queries often repeated
    add_timeout_hint=True,
    default_timeout=300000,  # 5 minutes for complex research queries
    add_query_hints=True,
    move_filters_to_service=True,
    enable_batching=True,
    batch_size=50,
    log_optimizations=True,
    log_performance_stats=True
)

PRODUCTION_CONFIG = OptimizationConfig(
    cache_enabled=True,
    cache_ttl=3600.0,  # 1 hour
    max_cache_entries=5000,  # Larger cache for production
    add_timeout_hint=True,
    default_timeout=60000,   # 1 minute - fail fast in production
    add_query_hints=True,
    move_filters_to_service=True,
    enable_batching=True,
    batch_size=100,
    log_optimizations=False,  # Reduce log noise in production
    log_cache_operations=False,
    log_performance_stats=True
)

DEVELOPMENT_CONFIG = OptimizationConfig(
    cache_enabled=False,  # Disable cache for development
    add_timeout_hint=True,
    default_timeout=30000,  # 30 seconds - fail fast during development
    add_query_hints=True,
    move_filters_to_service=False,  # Keep original structure for debugging
    log_optimizations=True,
    log_cache_operations=True,
    log_performance_stats=True
)

# Configuration presets
CONFIGS = {
    'diamm': DIAMM_CONFIG,
    'research': RESEARCH_CONFIG,
    'production': PRODUCTION_CONFIG,
    'development': DEVELOPMENT_CONFIG,
    'default': DIAMM_CONFIG
}


def get_config(name: str = 'default') -> OptimizationConfig:
    """
    Get a predefined configuration by name.
    
    Args:
        name: Configuration name ('diamm', 'research', 'production', 'development', 'default')
        
    Returns:
        OptimizationConfig instance
        
    Raises:
        ValueError: If configuration name is not found
    """
    if name not in CONFIGS:
        available = ', '.join(CONFIGS.keys())
        raise ValueError(f"Unknown configuration '{name}'. Available: {available}")
    
    return CONFIGS[name]


def create_custom_config(**kwargs) -> OptimizationConfig:
    """
    Create a custom configuration by overriding default values.
    
    Args:
        **kwargs: Configuration parameters to override
        
    Returns:
        OptimizationConfig instance with custom settings
        
    Example:
        config = create_custom_config(
            cache_ttl=1800.0,
            default_timeout=60000,
            log_optimizations=False
        )
    """
    base_config = DIAMM_CONFIG
    config_dict = base_config.__dict__.copy()
    config_dict.update(kwargs)
    return OptimizationConfig(**config_dict)


def get_config_summary(config: OptimizationConfig) -> str:
    """
    Get a human-readable summary of a configuration.
    
    Args:
        config: OptimizationConfig instance
        
    Returns:
        Formatted configuration summary
    """
    return f"""
Optimization Configuration Summary:
=====================================

Cache Settings:
  • Cache enabled: {config.cache_enabled}
  • Cache TTL: {config.cache_ttl}s ({config.cache_ttl/3600:.1f}h)
  • Max cache entries: {config.max_cache_entries}

Query Optimization:
  • Add timeout hints: {config.add_timeout_hint}
  • Default timeout: {config.default_timeout}ms ({config.default_timeout/1000:.0f}s)
  • Add query hints: {config.add_query_hints}
  • Move filters to SERVICE: {config.move_filters_to_service}
  • Runtime optimizer: {config.add_runtime_optimizer}
  • Max parallel requests: {config.max_parallel_requests}

Performance Features:
  • Enable batching: {config.enable_batching}
  • Batch size: {config.batch_size}
  • Early termination: {config.enable_early_termination}

Logging:
  • Log optimizations: {config.log_optimizations}
  • Log cache operations: {config.log_cache_operations}
  • Log performance stats: {config.log_performance_stats}
""".strip()