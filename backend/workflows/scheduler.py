import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel
import uuid

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScheduledTask(BaseModel):
    """A scheduled workflow task"""
    id: str
    workflow_id: str
    name: str
    trigger_type: str  # "cron", "interval", "date"
    trigger_config: Dict[str, Any]
    variables: Dict[str, Any] = {}
    enabled: bool = True
    created_at: datetime = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)


class WorkflowScheduler:
    """
    Scheduler for running workflows on a schedule.
    Supports cron expressions, intervals, and one-time runs.
    Persists scheduled tasks to database for recovery after restarts.
    """

    def __init__(self, workflow_engine=None, workflow_manager=None, db_session_factory=None):
        self.workflow_engine = workflow_engine
        self.workflow_manager = workflow_manager
        self.db_session_factory = db_session_factory
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.event_handlers: List[Callable] = []

        if SCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
        else:
            self.scheduler = None

    async def load_persisted_tasks(self):
        """Load scheduled tasks from database on startup"""
        if not self.db_session_factory:
            logger.warning("No database session factory configured, skipping persistence load")
            return

        try:
            from database.models import ScheduledTaskModel

            with self.db_session_factory() as session:
                db_tasks = session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.enabled == True
                ).all()

                loaded_count = 0
                for db_task in db_tasks:
                    try:
                        task = ScheduledTask(
                            id=db_task.id,
                            workflow_id=db_task.workflow_id,
                            name=db_task.name,
                            trigger_type=db_task.trigger_type,
                            trigger_config=json.loads(db_task.trigger_config),
                            variables=json.loads(db_task.variables) if db_task.variables else {},
                            enabled=db_task.enabled,
                            created_at=db_task.created_at,
                            last_run=db_task.last_run,
                            run_count=db_task.run_count
                        )

                        # Skip date triggers that have already passed
                        if task.trigger_type == "date":
                            run_date = task.trigger_config.get("run_date")
                            if run_date and isinstance(run_date, str):
                                run_date = datetime.fromisoformat(run_date)
                            if run_date and run_date < datetime.now(timezone.utc):
                                logger.info(f"Skipping expired date task: {task.name}")
                                continue

                        # Recreate the trigger and add to scheduler
                        trigger = self._create_trigger(task.trigger_type, task.trigger_config)
                        if trigger and SCHEDULER_AVAILABLE:
                            job = self.scheduler.add_job(
                                self._run_workflow,
                                trigger=trigger,
                                args=[task],
                                id=task.id,
                                name=task.name
                            )
                            task.next_run = job.next_run_time

                        self.scheduled_tasks[task.id] = task
                        loaded_count += 1

                    except Exception as e:
                        logger.error(f"Failed to load scheduled task {db_task.id}: {e}")

                logger.info(f"Loaded {loaded_count} scheduled tasks from database")

        except ImportError:
            logger.warning("Could not import ScheduledTaskModel, persistence unavailable")
        except Exception as e:
            logger.error(f"Failed to load persisted tasks: {e}")

    def _persist_task(self, task: ScheduledTask):
        """Save or update a task in the database"""
        if not self.db_session_factory:
            return

        try:
            from database.models import ScheduledTaskModel

            with self.db_session_factory() as session:
                db_task = session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.id == task.id
                ).first()

                if db_task:
                    # Update existing
                    db_task.workflow_id = task.workflow_id
                    db_task.name = task.name
                    db_task.trigger_type = task.trigger_type
                    db_task.trigger_config = json.dumps(task.trigger_config)
                    db_task.variables = json.dumps(task.variables)
                    db_task.enabled = task.enabled
                    db_task.last_run = task.last_run
                    db_task.next_run = task.next_run
                    db_task.run_count = task.run_count
                else:
                    # Create new
                    db_task = ScheduledTaskModel(
                        id=task.id,
                        workflow_id=task.workflow_id,
                        name=task.name,
                        trigger_type=task.trigger_type,
                        trigger_config=json.dumps(task.trigger_config),
                        variables=json.dumps(task.variables),
                        enabled=task.enabled,
                        created_at=task.created_at,
                        last_run=task.last_run,
                        next_run=task.next_run,
                        run_count=task.run_count
                    )
                    session.add(db_task)

                session.commit()

        except Exception as e:
            logger.error(f"Failed to persist task {task.id}: {e}")

    def _delete_persisted_task(self, task_id: str):
        """Remove a task from the database"""
        if not self.db_session_factory:
            return

        try:
            from database.models import ScheduledTaskModel

            with self.db_session_factory() as session:
                session.query(ScheduledTaskModel).filter(
                    ScheduledTaskModel.id == task_id
                ).delete()
                session.commit()

        except Exception as e:
            logger.error(f"Failed to delete persisted task {task_id}: {e}")

    def add_event_handler(self, handler: Callable):
        self.event_handlers.append(handler)

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        for handler in self.event_handlers:
            try:
                handler({"type": event_type, "data": data})
            except Exception as e:
                logger.warning(f"Event handler failed: {e}")

    async def schedule(
        self,
        workflow_id: str,
        name: str,
        trigger_type: str,
        trigger_config: Dict[str, Any],
        variables: Dict[str, Any] = None
    ) -> Optional[ScheduledTask]:
        """Schedule a workflow for recurring execution"""
        if not SCHEDULER_AVAILABLE:
            return None

        task_id = str(uuid.uuid4())[:12]

        task = ScheduledTask(
            id=task_id,
            workflow_id=workflow_id,
            name=name,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            variables=variables or {}
        )

        # Create trigger
        trigger = self._create_trigger(trigger_type, trigger_config)
        if not trigger:
            return None

        # Add job to scheduler
        job = self.scheduler.add_job(
            self._run_workflow,
            trigger=trigger,
            args=[task],
            id=task_id,
            name=name
        )

        task.next_run = job.next_run_time
        self.scheduled_tasks[task_id] = task

        # Persist to database
        self._persist_task(task)

        self.emit_event("task_scheduled", {
            "task_id": task_id,
            "workflow_id": workflow_id,
            "next_run": task.next_run.isoformat() if task.next_run else None
        })

        return task

    def _create_trigger(self, trigger_type: str, config: Dict[str, Any]):
        """Create an APScheduler trigger"""
        if not SCHEDULER_AVAILABLE:
            return None

        if trigger_type == "cron":
            return CronTrigger(
                minute=config.get("minute", "*"),
                hour=config.get("hour", "*"),
                day=config.get("day", "*"),
                month=config.get("month", "*"),
                day_of_week=config.get("day_of_week", "*")
            )

        elif trigger_type == "interval":
            return IntervalTrigger(
                seconds=config.get("seconds", 0),
                minutes=config.get("minutes", 0),
                hours=config.get("hours", 0),
                days=config.get("days", 0)
            )

        elif trigger_type == "date":
            run_date = config.get("run_date")
            if isinstance(run_date, str):
                run_date = datetime.fromisoformat(run_date)
            return DateTrigger(run_date=run_date)

        return None

    async def _run_workflow(self, task: ScheduledTask):
        """Execute a scheduled workflow"""
        self.emit_event("scheduled_run_started", {
            "task_id": task.id,
            "workflow_id": task.workflow_id
        })

        try:
            # Get workflow
            workflow = await self.workflow_manager.get(task.workflow_id)
            if not workflow:
                self.emit_event("scheduled_run_failed", {
                    "task_id": task.id,
                    "error": "Workflow not found"
                })
                return

            # Execute
            execution = await self.workflow_engine.execute(
                workflow,
                initial_context=task.variables
            )

            # Update task stats
            task.last_run = datetime.now(timezone.utc)
            task.run_count += 1

            # Update next run time
            if SCHEDULER_AVAILABLE and task.id in self.scheduled_tasks:
                job = self.scheduler.get_job(task.id)
                if job:
                    task.next_run = job.next_run_time

            # Persist updated stats
            self._persist_task(task)

            self.emit_event("scheduled_run_completed", {
                "task_id": task.id,
                "execution_id": execution.id,
                "status": execution.status
            })

        except Exception as e:
            self.emit_event("scheduled_run_failed", {
                "task_id": task.id,
                "error": str(e)
            })

    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a scheduled task by ID"""
        return self.scheduled_tasks.get(task_id)

    async def list_tasks(self) -> List[ScheduledTask]:
        """List all scheduled tasks"""
        return list(self.scheduled_tasks.values())

    async def pause(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        if not SCHEDULER_AVAILABLE:
            return False

        task = self.scheduled_tasks.get(task_id)
        if not task:
            return False

        self.scheduler.pause_job(task_id)
        task.enabled = False

        # Persist disabled state
        self._persist_task(task)

        self.emit_event("task_paused", {"task_id": task_id})
        return True

    async def resume(self, task_id: str) -> bool:
        """Resume a paused task"""
        if not SCHEDULER_AVAILABLE:
            return False

        task = self.scheduled_tasks.get(task_id)
        if not task:
            return False

        self.scheduler.resume_job(task_id)
        task.enabled = True

        job = self.scheduler.get_job(task_id)
        if job:
            task.next_run = job.next_run_time

        # Persist enabled state
        self._persist_task(task)

        self.emit_event("task_resumed", {"task_id": task_id})
        return True

    async def cancel(self, task_id: str) -> bool:
        """Cancel and remove a scheduled task"""
        if task_id not in self.scheduled_tasks:
            return False

        if SCHEDULER_AVAILABLE:
            self.scheduler.remove_job(task_id)

        del self.scheduled_tasks[task_id]

        # Remove from database
        self._delete_persisted_task(task_id)

        self.emit_event("task_cancelled", {"task_id": task_id})
        return True

    async def run_now(self, task_id: str) -> bool:
        """Trigger immediate execution of a scheduled task"""
        task = self.scheduled_tasks.get(task_id)
        if not task:
            return False

        # Run in background
        asyncio.create_task(self._run_workflow(task))
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total = len(self.scheduled_tasks)
        enabled = sum(1 for t in self.scheduled_tasks.values() if t.enabled)

        return {
            "total_tasks": total,
            "enabled_tasks": enabled,
            "disabled_tasks": total - enabled,
            "total_runs": sum(t.run_count for t in self.scheduled_tasks.values()),
            "scheduler_running": self.scheduler.running if SCHEDULER_AVAILABLE else False
        }

    def shutdown(self):
        """Shutdown the scheduler"""
        if SCHEDULER_AVAILABLE and self.scheduler:
            self.scheduler.shutdown()
