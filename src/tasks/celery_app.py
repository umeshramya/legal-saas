"""
Celery application configuration for background tasks.
This is a placeholder - actual task implementations will be added later.
"""
import os
from celery import Celery
from src.config import settings

# Create Celery application
celery_app = Celery(
    "legal_saas",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        # Task modules will be added here
        "src.tasks.document_tasks",
        "src.tasks.ai_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
)

# Optional: Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Example: Clean up temporary files every day
    # "cleanup-temp-files": {
    #     "task": "src.tasks.maintenance.cleanup_temp_files",
    #     "schedule": 86400.0,  # Every 24 hours
    # },
}

if __name__ == "__main__":
    celery_app.start()