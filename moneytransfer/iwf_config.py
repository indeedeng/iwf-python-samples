from iwf.client import Client
from iwf.registry import Registry
from iwf.worker_service import (
    WorkerService,
)

from moneytransfer.money_transfer_workflow import MoneyTransferWorkflow

registry = Registry()
worker_service = WorkerService(registry)
client = Client(registry, )

registry.add_workflow(MoneyTransferWorkflow())
