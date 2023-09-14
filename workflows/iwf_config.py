from iwf.client import Client
from iwf.registry import Registry
from iwf.worker_service import (
    WorkerService,
)

from workflows.signup_workflow import BasicWorkflow

registry = Registry()
worker_service = WorkerService(registry)
client = Client(registry)

registry.add_workflow(BasicWorkflow())
