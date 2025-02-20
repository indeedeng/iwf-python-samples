from dataclasses import dataclass
from random import randint
from datetime import timedelta
from iwf.workflow import ObjectWorkflow
from iwf.workflow_state import WorkflowState
from iwf.state_schema import StateSchema
from iwf.persistence_schema import PersistenceField, PersistenceSchema
from iwf.communication_schema import CommunicationSchema
from iwf.state_decision import StateDecision
from iwf.command_request import CommandRequest, TimerCommand
from iwf.command_results import CommandResults
from iwf.persistence import Persistence
from iwf.communication import Communication
from iwf.workflow_context import WorkflowContext
from iwf.rpc import rpc
from controller_workflow import Request
from controller_workflow import ControllerWorkflow
from iwf_config import client
from iwf.errors import WorkflowNotExistsError

PARENT_WORKFLOW_ID = "ParentWorkflowId"
PROCESSING_STATUS = "Status"


class ProcessingWorkflow(ObjectWorkflow):
    def get_workflow_states(self) -> StateSchema:
        return StateSchema.with_starting_state(FooState(), CompleteState())

    def get_persistence_schema(self) -> PersistenceSchema:
        return PersistenceSchema.create(
            PersistenceField.data_attribute_def(PARENT_WORKFLOW_ID, str),
            PersistenceField.data_attribute_def(PROCESSING_STATUS, str),
        )
    
    @rpc()
    def describe(self, child_workflow_id: str, persistence: Persistence)->str:
        return persistence.get_data_attribute(PROCESSING_STATUS)


class FooState(WorkflowState[Request]):
    def wait_until(self, ctx: WorkflowContext, input: Request, persistence: Persistence, communication: Communication) -> CommandRequest:
        persistence.set_data_attribute(PROCESSING_STATUS, "started")
        random_duration = randint(1, 30)
        # use a timer to simulate some long processing logic...
        return CommandRequest.for_any_command_completed(
            TimerCommand.timer_command_by_duration(timedelta(seconds=random_duration))
        )

    def execute(self, ctx: WorkflowContext, input: Request, command_results: CommandResults, persistence: Persistence, communication: Communication) -> StateDecision:
        persistence.set_data_attribute(PROCESSING_STATUS, "completed")
        return StateDecision.single_next_state(CompleteState)

class CompleteState(WorkflowState[None]):
    def execute(self, ctx: WorkflowContext, input: None, command_results: CommandResults, persistence: Persistence, communication: Communication) -> StateDecision:
        parent_workflow_id = persistence.get_data_attribute(PARENT_WORKFLOW_ID)
        
        try:
            client.invoke_rpc(parent_workflow_id, ControllerWorkflow.complete_child_workflow)
        except WorkflowNotExistsError:
            print("Parent workflow may have completed, possibly a duplicate completion request, ignoring it.")
        
        return StateDecision.graceful_complete_workflow()
