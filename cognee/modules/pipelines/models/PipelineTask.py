from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, UUID, ForeignKey
from cognee.infrastructure.databases.relational import Base

class PipelineTask(Base):
    __tablename__ = "pipeline_task"

    id = Column(UUID, primary_key = True, default = uuid4)

    created_at = Column(DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    pipeline_id = Column("pipeline", UUID, ForeignKey("pipeline.id"), primary_key = True)
    task_id = Column("task", UUID, ForeignKey("task.id"), primary_key = True)
