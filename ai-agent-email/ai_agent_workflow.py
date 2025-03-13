from iwf.command_request import CommandRequest, TimerCommand, InternalChannelCommand
from iwf.command_results import CommandResults
from iwf.communication import Communication
from iwf.communication_schema import CommunicationSchema, CommunicationMethod
from iwf.iwf_api.models import RetryPolicy, ChannelRequestStatus
from iwf.persistence import Persistence
from iwf.persistence_schema import PersistenceSchema, PersistenceField
from iwf.state_decision import StateDecision
from iwf.state_schema import StateSchema
from iwf.workflow import ObjectWorkflow
from iwf.workflow_context import WorkflowContext
from iwf.workflow_state import WorkflowState
from iwf.workflow_state_options import WorkflowStateOptions


class EmailAgentWorkflow(ObjectWorkflow):
    def get_persistence_schema(self) -> PersistenceSchema:
        return PersistenceSchema.create(
            PersistenceField.data_attribute_def(DA_STATUS, str),
            PersistenceField.data_attribute_def(DA_CURRENT_REQUEST, str),
            PersistenceField.data_attribute_def(DA_CURRENT_REQUEST_DRAFT, str),
            PersistenceField.data_attribute_def(DA_PREVIOUS_RESPONSE_ID, str),
            PersistenceField.data_attribute_def(DA_EMAIL_RECIPIENT, str),
            PersistenceField.data_attribute_def(DA_EMAIL_SUBJECT, str),
            PersistenceField.data_attribute_def(DA_EMAIL_BODY, str),
            PersistenceField.data_attribute_def(DA_SCHEDULED_TIME_SECONDS, int)
        )

    def get_communication_schema(self) -> CommunicationSchema:
        return CommunicationSchema.create(
            CommunicationMethod.internal_channel_def(CH_USER_INPUT, str),
        )

    def get_workflow_states(self) -> StateSchema:
        return StateSchema.with_starting_state(
            InitState(),
            AgentState(),
            ScheduleState(),
            SendingState()
        )


# represents the status of the current workflow execution, is one of below:
# initialized, processing, waiting, sent
DA_STATUS = "Status"
STATUS_INITIALIZED = "initialized"
STATUS_WAITING = "waiting"
STATUS_SENT = "sent"

# store the request from user
DA_CURRENT_REQUEST = "CurrentRequest"
# store the request draft from user(automatically store/restore for user)
DA_CURRENT_REQUEST_DRAFT = "RequestDraft"
# store the last response id fom openai response API call
DA_PREVIOUS_RESPONSE_ID = "PreviousResponseId"
# store the generated email recipient
DA_EMAIL_RECIPIENT = "EmailRecipient"
# store the generated email subject
DA_EMAIL_SUBJECT = "EmailSubject"
# store the generated email body
DA_EMAIL_BODY = "EmailBody"
# store the generated scheduled time to send the email
DA_SCHEDULED_TIME_SECONDS = "ScheduledTime"

# a channel to send text request from user(to approve/revise/cancel the email)
CH_USER_INPUT = "UserInput"


class InitState(WorkflowState[None]):
    def execute(
            self,
            ctx: WorkflowContext,
            ignored: None,
            command_results: CommandResults,
            persistence: Persistence,
            communication: Communication,
    ) -> StateDecision:
        persistence.set_data_attribute(DA_STATUS, STATUS_INITIALIZED)
        print(f"workflow started, id: {ctx.workflow_id}")

        return StateDecision.single_next_state(AgentState)


class AgentState(WorkflowState[None]):
    def wait_until(self, ctx: WorkflowContext, ignored: None, persistence: Persistence,
                   communication: Communication) -> CommandRequest:
        persistence.set_data_attribute(DA_STATUS, STATUS_WAITING)
        return CommandRequest.for_any_command_completed(
            # here use a timer to build reminder
            # Here user 30 seconds for testing, but it can be extended as needed:
            # IWF timer is durable, meaning it won't be lost on any instance restarts
            TimerCommand.by_seconds(30),
            InternalChannelCommand.by_name(CH_USER_INPUT)
        )

    def execute(self, ctx: WorkflowContext, ignored: None, command_results: CommandResults, persistence: Persistence,
                communication: Communication) -> StateDecision:
        if command_results.internal_channel_commands[0].status != ChannelRequestStatus.RECEIVED:
            # this means the timer has fired
            print("send an alert to user to complete the request :)")
            return StateDecision.single_next_state(AgentState)
        # TODO, use openAI response API to process the request
        send_time = 0
        persistence.set_data_attribute(DA_SCHEDULED_TIME_SECONDS, send_time)
        if send_time == 0:
            # means send now
            return StateDecision.single_next_state(SendingState)
        elif send_time > 0:
            # means scheduled
            return StateDecision.single_next_state(ScheduleState)
        else:
            # get the request again
            return StateDecision.single_next_state(AgentState)

    def get_state_options(self) -> WorkflowStateOptions:
        return WorkflowStateOptions(
            # customize the timeout to let OpenAI run longer
            execute_api_timeout_seconds=90
        )


class SendingState(WorkflowState[None]):
    def execute(
            self,
            ctx: WorkflowContext,
            ignored: None,
            command_results: CommandResults,
            persistence: Persistence,
            communication: Communication,
    ) -> StateDecision:
        persistence.set_data_attribute(DA_STATUS, STATUS_SENT)
        # TODO send the email here
        return StateDecision.graceful_complete_workflow()

    def get_state_options(self) -> WorkflowStateOptions:
        return WorkflowStateOptions(
            # customize the backoff retry policy for sending email API
            # by default it will retry forever
            # in case of wrong API key, we want to stop it after a minute
            execute_api_retry_policy=RetryPolicy(
                maximum_attempts_duration_seconds=60,
            )
        )


class ScheduleState(WorkflowState[None]):
    def wait_until(self, ctx: WorkflowContext, ignored: None, persistence: Persistence,
                   communication: Communication) -> CommandRequest:
        persistence.set_data_attribute(DA_STATUS, STATUS_WAITING)
        send_time = persistence.get_data_attribute(DA_SCHEDULED_TIME_SECONDS)
        # TODO calculate the timer duration
        duration = 1
        return CommandRequest.for_any_command_completed(
            TimerCommand.by_seconds(duration),
            # user can interrupt it anytime
            InternalChannelCommand.by_name(CH_USER_INPUT)
        )

    def execute(self, ctx: WorkflowContext, ignored: None, command_results: CommandResults, persistence: Persistence,
                communication: Communication) -> StateDecision:
        if command_results.internal_channel_commands[0].status == ChannelRequestStatus.RECEIVED:
            # TODO process user input again
            send_time = 0
            persistence.set_data_attribute(DA_SCHEDULED_TIME_SECONDS, send_time)
            if send_time == 0:
                # means send now
                return StateDecision.single_next_state(SendingState)
            else:
                # means scheduled
                return StateDecision.single_next_state(ScheduleState)
        else:
            # timer fired
            return StateDecision.single_next_state(SendingState)

    def get_state_options(self) -> WorkflowStateOptions:
        return WorkflowStateOptions(
            # customize the timeout to let OpenAI run longer
            execute_api_timeout_seconds=90
        )
