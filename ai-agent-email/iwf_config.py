from iwf.client import Client
from iwf.registry import Registry
from iwf.worker_service import (
    WorkerService,
)

from ai_agent_workflow import EmailAgentWorkflow

registry = Registry()
worker_service = WorkerService(registry)
client = Client(registry)

registry.add_workflow(EmailAgentWorkflow())
