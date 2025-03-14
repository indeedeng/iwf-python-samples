import os
import smtplib

from agents import AgentOutputSchema
from agents.models.openai_responses import Converter
from iwf.command_request import CommandRequest, TimerCommand, InternalChannelCommand
from iwf.command_results import CommandResults
from iwf.communication import Communication
from iwf.communication_schema import CommunicationSchema, CommunicationMethod
from iwf.iwf_api.models import RetryPolicy, ChannelRequestStatus
from iwf.persistence import Persistence
from iwf.persistence_schema import PersistenceSchema, PersistenceField
from iwf.rpc import rpc
from iwf.state_decision import StateDecision
from iwf.state_schema import StateSchema
from iwf.workflow import ObjectWorkflow
from iwf.workflow_context import WorkflowContext
from iwf.workflow_state import WorkflowState
from iwf.workflow_state_options import WorkflowStateOptions
from openai import OpenAI
from pydantic import BaseModel


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

    @rpc()
    def send_request(self, ctx: WorkflowContext, input: str, persistence: Persistence,
                     communication: Communication) -> bool:
        status = persistence.get_data_attribute(DA_STATUS)
        if status == STATUS_WAITING:
            communication.publish_to_internal_channel(CH_USER_INPUT, input)
            return True
        else:
            return False


# represents the status of the current workflow execution, is one of below:
# initialized, waiting, scheduled, sent, failed
DA_STATUS = "Status"
STATUS_INITIALIZED = "initialized"
STATUS_WAITING = "waiting"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"

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

        google_email = os.environ.get('GOOGLE_EMAIL_ADDRESS')
        google_email_app_password = os.environ.get('GOOGLE_EMAIL_APP_PASSWORD')

        if not google_email or not google_email_app_password:
            persistence.set_data_attribute(DA_STATUS, STATUS_FAILED)
            raise StateDecision.force_fail_workflow("not provided google email credentials")
        return StateDecision.single_next_state(AgentState)


class AgentState(WorkflowState[None]):
    def wait_until(self, ctx: WorkflowContext, ignored: None, persistence: Persistence,
                   communication: Communication) -> CommandRequest:
        persistence.set_data_attribute(DA_STATUS, STATUS_WAITING)
        return CommandRequest.for_any_command_completed(
            InternalChannelCommand.by_name(CH_USER_INPUT)
        )

    def execute(self, ctx: WorkflowContext, ignored: None, command_results: CommandResults, persistence: Persistence,
                communication: Communication) -> StateDecision:
        user_req = command_results.internal_channel_commands[0].value
        agent_response = process_user_request(user_req, persistence)
        if agent_response.cancel_operation:
            return StateDecision.graceful_complete_workflow("cancel emailing")

        if agent_response.email_send_time_unix_seconds > 0:
            persistence.set_data_attribute(DA_SCHEDULED_TIME_SECONDS, agent_response.email_send_time_unix_seconds)
        if agent_response.email_body:
            persistence.set_data_attribute(DA_EMAIL_BODY, agent_response.email_body)
        if agent_response.email_subject:
            persistence.set_data_attribute(DA_EMAIL_SUBJECT, agent_response.email_subject)
        if agent_response.email_recipient:
            persistence.set_data_attribute(DA_EMAIL_RECIPIENT, agent_response.email_recipient)

        send_time = persistence.get_data_attribute(DA_SCHEDULED_TIME_SECONDS)
        recipient = persistence.get_data_attribute(DA_EMAIL_RECIPIENT)
        body = persistence.get_data_attribute(DA_EMAIL_BODY)
        if send_time > 0 and recipient and body:
            # now we can schedule to send email
            return StateDecision.single_next_state(ScheduleState)
        else:
            # otherwise get another request from user
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
        google_email = os.environ.get('GOOGLE_EMAIL_ADDRESS')
        google_email_app_password = os.environ.get('GOOGLE_EMAIL_APP_PASSWORD')

        smtp_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtp_server.ehlo()
        smtp_server.login(google_email, google_email_app_password)

        sent_to = persistence.get_data_attribute(DA_EMAIL_RECIPIENT)
        subject = persistence.get_data_attribute(DA_EMAIL_SUBJECT)
        body = persistence.get_data_attribute(DA_EMAIL_BODY)

        message = 'Subject: {}\n\n{}'.format(subject, body)

        smtp_server.sendmail(google_email, sent_to, message)
        smtp_server.quit()

        persistence.set_data_attribute(DA_STATUS, STATUS_SENT)
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
        return CommandRequest.for_any_command_completed(
            # timer in iWF is durable, meaning that it will not be lost for any instance restarts
            TimerCommand.by_seconds(get_timer_duration(send_time)),
            # user can interrupt it anytime when waiting
            InternalChannelCommand.by_name(CH_USER_INPUT)
        )

    def execute(self, ctx: WorkflowContext, ignored: None, command_results: CommandResults, persistence: Persistence,
                communication: Communication) -> StateDecision:
        if command_results.internal_channel_commands[0].status == ChannelRequestStatus.RECEIVED:
            # Go to agent state to process user input again
            # put the message back to the channel so that we can reuse the AgentState to process it.
            # Alternatively, we can process it in this state, but the code will be a little more complex.
            communication.publish_to_internal_channel(CH_USER_INPUT, command_results.internal_channel_commands[0].value)
            return StateDecision.single_next_state(AgentState)
        else:
            # timer fired
            return StateDecision.single_next_state(SendingState)

    def get_state_options(self) -> WorkflowStateOptions:
        return WorkflowStateOptions(
            # customize the timeout to let OpenAI run longer
            execute_api_timeout_seconds=90
        )


class AgentResponse(BaseModel):
    email_recipient: str | None
    email_subject: str | None
    email_body: str | None
    email_send_time_unix_seconds: int | None
    cancel_operation: bool | None


def process_user_request(req: str, persistence: Persistence) -> AgentResponse:
    response = do_process_user_request(req, persistence.get_data_attribute(DA_PREVIOUS_RESPONSE_ID))
    if isinstance(response.id, str):
        persistence.set_data_attribute(DA_PREVIOUS_RESPONSE_ID, response.id)

    resp = response.output[0].content[0].text
    return AgentResponse.model_validate_json(resp)


def do_process_user_request(req: str, previous_response_id: str | None):
    client = OpenAI()

    response = client.responses.create(
        model="gpt-4o",
        instructions="""
        Help prepare an email to be sent. Based on user requests, return email's subject, body, recipient 
        , sending time and/or cancel_operation, if any of them available. 
        The email subject or body may need to be translated if user requests to.
        The email subject and body should be complete, do not leave any place holders there. 
        The email's recipient should be in a valid email format, other wise, return empty string for that field.
        The sending time must be in unix timestamp in seconds, for example, 1741928839. 
        User may provide an relative time based on today/now, you should calculate the timestamp based on offset. For example, tomorrow means current timestamp plus 86400.
        User may also ask to cancel the emailing operation, then return true for cancel_operation field.
        All the fields are optional.
        If there is no recipient, return empty string for the field.
        If there is no body, return empty string for the field.
        If there is no subject, return empty string for the field.
        If there is no sending time, return 0 for the field.
        If not asking to cancel emailing, return false for the field.
        """,
        input=req,
        text=Converter.get_response_format(
            AgentOutputSchema(AgentResponse)
        ),
        previous_response_id=previous_response_id
    )
    from pprint import pprint
    pprint(response)
    return response


def get_timer_duration(send_time: int) -> int:
    # calculate duration based on current time
    import time
    current_time = int(time.time())
    duration = max(0, send_time - current_time)  # Ensure the duration is non-negative
    return duration
