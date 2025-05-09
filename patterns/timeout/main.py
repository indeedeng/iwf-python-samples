import asyncio
import sys
from iwf.client import Client
from iwf.registry import Registry
from iwf.iwf_api.models import WorkflowOptions

from handle_timeout_workflow import HandlingTimeoutWorkflow
from iwf_config import IWF_SERVER_URL, REGISTRY_NAMESPACE

# Create registry
registry = Registry(REGISTRY_NAMESPACE)

# Register workflow
registry.add_workflow(HandlingTimeoutWorkflow())

# Create client
client = Client(IWF_SERVER_URL)


async def start_workflow():
    # Start a workflow
    workflow_id = "handling-timeout-workflow-" + str(hash(str(sys.argv)))
    workflow_options = WorkflowOptions(workflow_id=workflow_id)

    # Start the workflow with no input
    await client.start_workflow(
        workflow_type=HandlingTimeoutWorkflow.__name__,
        workflow_options=workflow_options,
        workflow_input=None
    )
    print(f"Started workflow with ID: {workflow_id}")


async def run_worker():
    # Start the worker
    await client.start_worker(registry)


async def main():
    # Start a workflow
    await start_workflow()

    # Run the worker
    await run_worker()


if __name__ == "__main__":
    asyncio.run(main())