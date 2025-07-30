#!/usr/bin/env python3
"""
AI Translation System - Entry Point
"""

import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import settings

if __name__ == "__main__":
    print("🚀 Starting AI Translation System...")
    print(f"📡 Server: http://{settings.api_host}:{settings.api_port}")
    print(f"🔧 LLM Provider: {settings.llm_provider}")
    print(f"📊 Database: {settings.database_url}")
    print(f"📚 Vector DB: {settings.vector_db_path}")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
