from iwf.client import Client
from iwf.registry import Registry
from iwf.worker_service import (
    WorkerService,
)

from controller_workflow import ControllerWorkflow
from processing_workflow import ProcessingWorkflow

registry = Registry()
worker_service = WorkerService(registry)
client = Client(registry)

registry.add_workflows(
    ControllerWorkflow(), 
    ProcessingWorkflow()
    )
