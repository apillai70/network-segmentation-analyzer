# -*- coding: utf-8 -*-
"""
Persistence Module
==================
Unified persistence layer with PostgreSQL and JSON support
"""

from .unified_persistence import UnifiedPersistenceManager, create_persistence_manager

__all__ = ['UnifiedPersistenceManager', 'create_persistence_manager']
