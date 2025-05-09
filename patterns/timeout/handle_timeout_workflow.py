from typing import List, Dict, Any, Optional
from datetime import timedelta

from iwf.workflow_state import WorkflowState
from iwf.state_decision import StateDecision
from iwf.object_workflow import ObjectWorkflow
from iwf.workflow_context import WorkflowContext
from iwf.state_def import StateDef
from iwf.command.command_request import CommandRequest
from iwf.command.command_results import CommandResults
from iwf.command.timer_command import TimerCommand


class InitState(WorkflowState):
    def get_state_options(self):
        return None

    async def execute(self, context: WorkflowContext, input_data: Optional[Any]) -> StateDecision:
        # Create a timer command that will trigger after 10 seconds
        timer_command = TimerCommand(fire_after=timedelta(seconds=10))
        command_request = CommandRequest(timer_commands=[timer_command])

        # Execute the command
        command_results = await context.command_client.execute_command(command_request)

        # Check if timer has fired
        if command_results.timer_results and command_results.timer_results[0].fired:
            # Timer fired, go to timeout state
            return StateDecision.single_next_state("TimeoutState")
        else:
            # Timer not fired, go to task state
            return StateDecision.single_next_state("TaskState")


class TimeoutState(WorkflowState):
    def get_state_options(self):
        return None

    async def execute(self, context: WorkflowContext, input_data: Optional[Any]) -> StateDecision:
        # Handle timeout logic here
        print("Handling timeout...")

        # Complete the workflow
        return StateDecision.graceful_complete_workflow(None)


class TaskState(WorkflowState):
    def get_state_options(self):
        return None

    async def execute(self, context: WorkflowContext, input_data: Optional[Any]) -> StateDecision:
        # Perform the task
        print("Performing the task...")

        # Complete the workflow
        return StateDecision.graceful_complete_workflow(None)


class HandlingTimeoutWorkflow(ObjectWorkflow):
    def get_workflow_states(self) -> List[StateDef]:
        return [
            StateDef.starting_state(InitState()),
            StateDef.non_starting_state(TimeoutState()),
            StateDef.non_starting_state(TaskState())
        ]