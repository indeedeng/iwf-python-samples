from dataclasses import dataclass
from typing import List
from iwf.workflow import ObjectWorkflow
from iwf.workflow_state import WorkflowState
from iwf.state_schema import StateSchema
from iwf.persistence_schema import PersistenceField, PersistenceSchema
from iwf.communication_schema import CommunicationSchema, CommunicationMethod
from iwf.state_decision import StateDecision
from iwf.command_request import CommandRequest, InternalChannelCommand
from iwf.command_results import CommandResults
from iwf.persistence import Persistence
from iwf.communication import Communication
from iwf.workflow_context import WorkflowContext
from iwf.rpc import rpc
from iwf.errors import WorkflowAlreadyStartedError
from iwf_config import client
from iwf.workflow_options import WorkflowOptions
from iwf.iwf_api.models import (
    IDReusePolicy,
    WorkflowAlreadyStartedOptions,
)

from processing_workflow import ProcessingWorkflow
from processing_workflow import PARENT_WORKFLOW_ID

@dataclass
class Request:
    id: str
    data: str

NUM_CONTROLLER_WORKFLOWS = 5 # max number of controller workflows, one per resource (e.g ec2 instance)
CONCURRENCY_PER_CONTROLLER_WORKFLOW = 5 # max number of requests that are being processed
MAX_BUFFERED_REQUESTS = 20 # max number of requests that are in the buffer

REQUEST_QUEUE = "RequestQueue"
CHILD_COMPLETE_CHANNEL_PREFIX = "ChildComplete_"
DA_CURRENT_WAIT_CHILD_WFS = "CurrentWaitChildWfs"



class ControllerWorkflow(ObjectWorkflow):
    def get_workflow_states(self) -> StateSchema:
        return StateSchema.with_starting_state(InitState(), LoopForNextRequestState())

    def get_persistence_schema(self) -> PersistenceSchema:
        return PersistenceSchema.create(
            PersistenceField.data_attribute_def(DA_CURRENT_WAIT_CHILD_WFS, List[str]), 
        )

    def get_communication_schema(self) -> CommunicationSchema:
        return CommunicationSchema.create(
            CommunicationMethod.internal_channel_def(REQUEST_QUEUE, Request),
            CommunicationMethod.internal_channel_def_by_prefix(CHILD_COMPLETE_CHANNEL_PREFIX, None),
        )
    

    @rpc()
    def enqueue(self, request: Request, communication: Communication) -> bool:
        if communication.get_internal_channel_size(REQUEST_QUEUE)+1 > MAX_BUFFERED_REQUESTS:
            return False
        
        communication.publish_internal_channel(REQUEST_QUEUE, request)
        return True

    @rpc()
    def complete_child_workflow(self, child_workflow_id: str, persistence: Persistence, communication: Communication):
        current_wait_child_wfs = persistence.get_data_attribute(DA_CURRENT_WAIT_CHILD_WFS) or []
        if child_workflow_id  not in current_wait_child_wfs:
            # this could be caused by some edge cases when server is overloaded by some timeout/backoff retry
            # checking here to avoid sending too many garbage to the channel.
            return
        communication.publish_internal_channel(CHILD_COMPLETE_CHANNEL_PREFIX + child_workflow_id, None)


class InitState(WorkflowState[Request]):
    def execute(self, ctx: WorkflowContext, input: Request, command_results: CommandResults, persistence: Persistence, communication: Communication) -> StateDecision:
        communication.publish_internal_channel(REQUEST_QUEUE, input)
        
        persistence.set_data_attribute(DA_CURRENT_WAIT_CHILD_WFS, [])
        
        return StateDecision.single_next_state(LoopForNextRequestState)


class LoopForNextRequestState(WorkflowState[None]):
    def wait_until(self, ctx: WorkflowContext, input: None, persistence: Persistence, communication: Communication) -> CommandRequest:
        current_wait_child_wfs = persistence.get_data_attribute(DA_CURRENT_WAIT_CHILD_WFS)
        commands = []
        if len(current_wait_child_wfs) < CONCURRENCY_PER_CONTROLLER_WORKFLOW:
            commands.append(InternalChannelCommand.by_name(REQUEST_QUEUE))
            # otherwise, don't get a new request because the concurrency limit is reached
        for child_wf_id in current_wait_child_wfs:
            # wait for every child workflow to complete
            commands.append(InternalChannelCommand.by_name(CHILD_COMPLETE_CHANNEL_PREFIX + child_wf_id))
        return CommandRequest.for_any_command_completed(*commands)

    def execute(self, ctx: WorkflowContext, input: None, command_results: CommandResults, persistence: Persistence, communication: Communication) -> StateDecision:
        current_wait_child_wfs = persistence.get_data_attribute(DA_CURRENT_WAIT_CHILD_WFS)
        new_wait_list = []
        
        for command_result in command_results.internal_channel_commands:
            channel_name = command_result.channel_name
            if channel_name == REQUEST_QUEUE:
                if command_result.status == "RECEIVED":
                    request = command_result.value
                    child_workflow_id = f"processing-{request.id}"
                    try:
                        client.start_workflow(
                            ProcessingWorkflow, child_workflow_id, 3600, request,
                            WorkflowOptions(
                                    initial_data_attributes={PARENT_WORKFLOW_ID:ctx.workflow_id},
                                    workflow_id_reuse_policy=IDReusePolicy.DISALLOW_REUSE,
                                    workflow_already_started_options=
                                        WorkflowAlreadyStartedOptions(
                                            ignore_already_started_error=True,
                                            request_id=ctx.child_workflow_request_id
                                            )
                                )
                            )
                        new_wait_list.append(child_workflow_id)
                    except WorkflowAlreadyStartedError:
                        # there could be edge cases caused by network timeout/retry
                        print("already started by other threads/runs, ignore it -- not waiting for it")
                        
            elif channel_name.startswith(CHILD_COMPLETE_CHANNEL_PREFIX):
                if command_result.status == "RECEIVED":
                    child_wf_id = channel_name[len(CHILD_COMPLETE_CHANNEL_PREFIX):]
                    new_wait_list.remove(child_wf_id)
        
        persistence.set_data_attribute(DA_CURRENT_WAIT_CHILD_WFS, new_wait_list)
        
        if not new_wait_list:
            # atomically check if we can close this workflow 
            return StateDecision.force_complete_if_internal_channel_empty_or_else(REQUEST_QUEUE, LoopForNextRequestState)
        return StateDecision.single_next_state(LoopForNextRequestState)
