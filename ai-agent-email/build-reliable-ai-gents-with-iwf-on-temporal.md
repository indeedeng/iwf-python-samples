# Build Reliable AI Agents with iWF on Temporal

## Overall

This article describe how to build a reliable AI agent using
iWF on Temporal.

This article demonstrates an architecture that is production-grade, capable of serving and operating on high-scale
traffic, resilient to errors such as instance or network failures, and emphasizes a design and implementation approach
that remains extremely simple to build and maintain.

## Demo requirements

The demo showcases an AI-powered email agent capable of composing, translating, and scheduling emails with auto-save
drafting and cancellation features. It utilizes iWF on Temporal to ensure high scalability, reliability, and seamless
integration with third-party APIs like OpenAI and Gmail for durable and stateful workflows.

[![AI Agent Email Demo](https://img.youtube.com/vi/2dvIetECHWg/0.jpg)](https://www.youtube.com/watch?v=2dvIetECHWg "AI Agent Email Demo")

[![iWF Framework Overview](https://img.youtube.com/vi/EEHSLYkbREU/0.jpg)](https://www.youtube.com/watch?v=EEHSLYkbREU "AI Agent Email Demo with Cancel")

### Functional requirements

- **AI-Powered Email Composition**: Generate professionally written emails based on simple user requests and inputs
- **Email Translation**: Translate emails into different languages upon request
- **Smart Scheduling**: Schedule emails to be sent at specific times, supporting both absolute and relative time
  expressions (e.g., "tomorrow", "in 2 hours")
- **Auto-Save Draft**: Automatically saves draft inputs every 5 seconds to prevent work loss
- **Cancel & Revise Operation**: Ability to cancel scheduled emails or revise them, before they're actually sent

### Technical requirements

- **Workflow Checkpointing**: Uses iWF to maintain workflow state, enabling resumption from previous points after any
  instance restart
- **Scalable Architecture**: Capable of handling **billions** of concurrent workflows
- **Durable Timers**: Schedule-based operations use server-side durable timers that persist across system restarts
- **Server-Side Backoff Retry**: Built-in retry mechanism orchestrated on the server side as distributed system, not
  dependent on a single machine.
- **Stateful Conversation Integration**: Seamless integration with OpenAI's GPT models with context retention
- **Durable Drafting System**: Preserves user input across page refreshes and browser sessions

### API definitions

Here’s a summary of
the [four APIs](https://github.com/indeedeng/iwf-python-samples/blob/39d9ee5d67c9b8dcfec012b61df62ec3f3fb15e5/ai-agent-email/main.py#L27)
exposed to the frontend:

1. **Start API**:  
   Initiates a new workflow execution by a workflowId as unique identifier of a workflow execution.
   A workflow execution represents the whole lifecycle of creating an email with agent.

2. **Describe API**:  
   Fetches the current state of a specific workflow using its unique identifier. It provides details like the current
   drafted email subject/body/recipient, auto-saved drafts.

3. **Request API**:  
   Receives user request as text message to interact with the agent. It can be drafting or scheduling an email,
   translating it, or canceling a previously scheduled email.

4. **Save Draft API**:  
   Saves the user's email draft to maintain durability across user sessions/devices.

## Architecture

<img width="710" alt="architecture" src="https://github.com/user-attachments/assets/7a1b30e6-7f7f-4780-872b-6239ea9ef174" />

The architecture of this demo ensures seamless integration between user interactions, backend services, and
third-party APIs to provide reliable AI-powered workflows with high scalability and durability.

1. **User Interaction**:
    - The user accesses the application through a web browser.

2. **Frontend (Browser)**:
    - Provides an intuitive interface for composing emails, translating them, scheduling emails, etc.
    - Sends requests and receives updates through asynchronous APIs.
    - Regularly auto-saves draft emails using periodic API calls and ensures a smooth experience.

3. **Backend (Python + Flask + iWF SDK + OpenAI SDK)**:
    - Acts as the main orchestrator for the application.
    - Built using Python and Flask, it handles incoming API requests, processes data, and triggers workflows.
    - Utilizes the **iWF SDK** for workflow orchestration and managing stateful operations.
    - Integrates with **OpenAI SDK** to generate content, make autonomy decisions etc.
    - Communicates with the **Gmail API** to send emails.

4. **iWF Server and Temporal**:
    - The iWF server and Temporal manages workflow state, schedules tasks, and ensure durability.

## Workflow Overview

<img width="901" alt="Workflow Overview" src="https://github.com/user-attachments/assets/06d8d95b-9242-461b-8694-2a4a6053ae35" />

The [AI Agent Email workflow](https://github.com/indeedeng/iwf-python-samples/blob/ai-agent/ai-agent-email/ai_agent_workflow.py)
is implemented using iWF (Indeed Workflow Framework), providing a robust state machine for
handling the entire email creation, scheduling, and delivery process. Let's break down how the workflow operates:

### Workflow States

The [workflow](https://github.com/indeedeng/iwf-python-samples/blob/ai-agent/ai-agent-email/ai_agent_workflow.py)
consists of four main states, each handling a specific part of the email lifecycle:

1. **InitState**: The entry point that initializes the workflow and verifies required credentials.
    - Sets initial status as "initialized"
    - Validates Google email credentials
    - Transitions to AgentState upon successful initialization

2. **AgentState**: The core interactive state where the AI agent processes user requests.
    - Sets status to "waiting" when ready for user input
    - Uses OpenAI's GPT model to handle user requests
    - Processes various actions like email drafting, translation, and scheduling
    - Updates email details based on agent responses
    - Can transition back to itself for further refinement or to ScheduleState when ready to schedule

3. **ScheduleState**: Handles email scheduling with durable timers.
    - Sets up a durable timer based on the scheduled send time
    - Allows users to interrupt with new inputs (cancellations or revisions)
    - Transitions to SendingState when the timer fires or back to AgentState if interrupted

4. **SendingState**: Responsible for the actual email delivery.
    - Connects to Gmail SMTP server
    - Sends the composed email
    - Marks the workflow as completed

### Key Workflow Components

1. **Persistence Schema**: Maintains the workflow state with durable data attributes:
    - Email details (recipient, subject, body)
    - Workflow status (initialized, waiting, processing, sent, failed, canceled)
    - Current user request and draft
    - Scheduled sending time

2. **Communication Schema**: Defines the channels for interaction:
    - Internal channel for user inputs that can interrupt the workflow

3. **RPC Methods**: Exposes API endpoints for interacting with the workflow:
    - `send_request(...)`: Processes new user requests
    - `describe()`: Returns the current state of the workflow
    - `save_draft(...)`: Persists the user's draft

4. **Agent Processing**: The `process_user_request()` function:
    - Maintains conversation context with previous response IDs
    - Interprets user requests and extracts email details
    - Handles special actions like cancellations
    - Returns structured data for workflow processing

### Reliability Features

1. **Error Handling**: Custom retry policies for external API interactions
    - Maximum attempt durations to prevent infinite retries

2. **Durable Timers**: Email scheduling that persists across restarts
    - The `get_timer_duration()` function calculates time differences safely

3. **State Management**: Clear state transitions with proper persistence
    - All state changes are recorded in the durable workflow storage

4. **Interruption Handling**: Users can interrupt scheduled emails
    - The ScheduleState monitors both timer completion and user interruptions

## Dive deep into implementation

Now let's start dive deep into the code.

### Workflow definition

```python
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
```

The workflow definition above forms the backbone of our AI agent implementation. It defines a structured schema that iWF
uses to create a reliable, durable, and scalable workflow. Let's understand the three key schema components:

#### 1. Persistence Schema

The `get_persistence_schema()` method defines all the data attributes that need to be persisted throughout the workflow
execution:

- **Structure**: Each attribute is defined with a name and type using `PersistenceField.data_attribute_def()`
- **Durability**: These attributes are automatically persisted by iWF in Temporal's durable storage
- **State Management**: Attributes include workflow status, email components, request history, and scheduling
  information
- **Type Safety**: Each attribute is strongly typed (string, integer) to ensure data consistency

#### 2. Communication Schema

The `get_communication_schema()` method defines
the [channels](https://github.com/indeedeng/iwf/wiki/WorkflowState#signalchannel--internalchannel-async-message-queue)
through which the workflow can receive inputs. The communication schema enables the interactive nature of our AI agent,
allowing users to send requests, make
revisions, or cancel operations while maintaining the workflow's durability.

#### 3. State Schema

The `get_workflow_states()` method defines the state machine that drives the workflow on the background(proactively
executing).

This state-based approach allows for clear separation of concerns, with each state handling specific aspects of the
email agent's lifecycle. The state transitions are explicit, making the workflow logic easy to understand and maintain.

Together, these schema components create a declarative definition of our workflow that iWF can interpret and execute
with strong reliability guarantees. The schema-based approach significantly reduces the amount of boilerplate code
needed for handling persistence, state management, and communication.

For a more comprehensive understanding of iWF workflow definitions and basic concepts, refer to
the [iWF Basic Concepts Overview documentation](https://github.com/indeedeng/iwf/wiki/Basic-concepts-overview). This
resource explains the core ideas behind iWF's approach to workflow definition and execution in greater detail.

### Workflow RPCs

```python
@rpc()
def send_request(self, input: str, persistence: Persistence, communication: Communication) -> bool:
    status = persistence.get_data_attribute(DA_STATUS)
    if status == STATUS_WAITING:
        persistence.set_data_attribute(DA_CURRENT_REQUEST_DRAFT, "")
        communication.publish_to_internal_channel(CH_USER_INPUT, input)
        persistence.set_data_attribute(DA_STATUS, STATUS_PROCESSING)
        return True
    else:
        return False


@rpc()
def describe(self, persistence: Persistence) -> WorkflowDetails:
    status = persistence.get_data_attribute(DA_STATUS)
    current_request = persistence.get_data_attribute(DA_CURRENT_REQUEST)
    current_request_draft = persistence.get_data_attribute(DA_CURRENT_REQUEST_DRAFT)
    response_id = persistence.get_data_attribute(DA_PREVIOUS_RESPONSE_ID)
    email_recipient = persistence.get_data_attribute(DA_EMAIL_RECIPIENT)
    email_subject = persistence.get_data_attribute(DA_EMAIL_SUBJECT)
    email_body = persistence.get_data_attribute(DA_EMAIL_BODY)
    send_time_seconds = persistence.get_data_attribute(DA_SCHEDULED_TIME_SECONDS)

    return WorkflowDetails(
        status=status,
        current_request=current_request,
        current_request_draft=current_request_draft,
        response_id=response_id,
        email_recipient=email_recipient,
        email_subject=email_subject,
        email_body=email_body,
        send_time_seconds=send_time_seconds
    )


@rpc()
def save_draft(self, draft: str, persistence: Persistence):
    persistence.set_data_attribute(DA_CURRENT_REQUEST_DRAFT, draft)
```

[Remote Procedure Calls (RPCs)](https://github.com/indeedeng/iwf/wiki/RPC)
are a critical component of the iWF framework that enable external systems to
interact with running workflow executions.
In our AI email agent, we use RPCs to create a bridge between the Flask web server
and the workflow executions running in the iWF/Temporal backend.

#### Our Email Agent RPCs

The AI email agent implements three critical RPCs:

1. **`send_request`**: Processes new user queries and requests to the AI agent
    - Takes the user's text input as a parameter
    - Checks if the workflow is in the "waiting" state before proceeding
    - Clears any existing draft text
    - Publishes the user input to the internal channel for the AgentState or ScheduleState to process
    - Updates the workflow status to "processing"
    - Returns a boolean indicating success or failure

2. **`describe`**: Provides a complete snapshot of the current workflow state
    - Retrieves all relevant data attributes from the persistence layer
    - Returns email details (recipient, subject, body), status, and other metadata
    - This RPC enables the frontend to display up-to-date information about the email

3. **`save_draft`**: Persists the user's draft text
    - Takes the draft text as a parameter
    - Saves it to the persistence layer for durability
    - Enables auto-save functionality in the UI

The RPCs in our implementation serve as the primary communication points between the frontend UI and the backend
workflow,
ensuring that user interactions are properly captured, processed, and reflected in the workflow state.
This approach makes our AI agent both interactive and reliable, handling real-time user inputs
while maintaining workflow durability.

### Workflow States

iWF WorkflowState is the unit of executing "asynchronous" on the "background".
It allows AI Agent to proactively perform operations on behalf of users.

#### InitState

```python
class InitState(WorkflowState[None]):
    def execute(
            ...
    ) -> StateDecision:
        persistence.set_data_attribute(DA_STATUS, STATUS_INITIALIZED)
        print(f"workflow started, id: {ctx.workflow_id}")

        google_email = os.environ.get('GOOGLE_EMAIL_ADDRESS')
        google_email_app_password = os.environ.get('GOOGLE_EMAIL_APP_PASSWORD')

        if not google_email or not google_email_app_password:
            persistence.set_data_attribute(DA_STATUS, STATUS_FAILED)
            raise StateDecision.force_fail_workflow("not provided google email credentials")
        return StateDecision.single_next_state(AgentState)
```

The InitState serves as the workflow's entry point, initializing the workflow status
and validating required credentials for email delivery. It checks for the presence of
Google email credentials (email address and app password) and fails the workflow
early if these required values are missing.

Upon successful initialization, it transitions to the AgentState where the AI agent
can begin processing user requests.

#### AgentState

```python
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
            persistence.set_data_attribute(DA_STATUS, STATUS_CANCELED)
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
        if send_time and send_time > 0 and recipient and body:
            # now we can schedule to send email
            return StateDecision.single_next_state(ScheduleState)
        else:
            # otherwise get another request from user
            return StateDecision.single_next_state(AgentState)
```

The AgentState serves as the interactive core of the workflow, waiting for user input and processing
requests using the OpenAI API to generate or modify email content. Upon receiving user input,
it intelligently handles various actions including email drafting, translation, scheduling,
or cancellation by persisting the appropriate data attributes to the workflow state.

Based on the completeness of the email details (recipient, subject, body, and send time),
it either transitions to the ScheduleState when ready to schedule an email or cycles back to
itself to await further user interaction.

```python
    def get_state_options(self) -> WorkflowStateOptions:


    return WorkflowStateOptions(
        # customize the timeout to let OpenAI run longer
        execute_api_timeout_seconds=90
    )
```

The `get_state_options` method
configures [special execution parameters](https://github.com/indeedeng/iwf/wiki/WorkflowOptions)
for the AgentState, extending the default API timeout to 90 seconds to accommodate potential latency when calling
OpenAI's API.

This customization is crucial for AI-powered workflows, where external API calls may take longer than standard timeouts
would allow, preventing premature failure of the workflow due to timeout constraints.

#### ScheduleState

```python
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
```

The ScheduleState exemplifies iWF's powerful durable timer capabilities and interruptibility features
for long-running operations. This state sets up a timer to wait until the scheduled send time
for the email while simultaneously listening for user interruptions (like cancellations or revisions).

When either the timer fires or a user input is received, the `execute` method determines which path to take:
proceeding to send the email if the timer completed, or returning to the AgentState to process a new user
request if an interruption occurred.

The durable nature of the timer ensures that even if the system restarts or experiences failures
during the scheduled waiting period (which could be hours or days), the timer will resume correctly
when the system recovers. This allows the email agent to reliably schedule emails far in advance
without worrying about system reliability issues.

#### SendingState

```python
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
```

```python
    def get_state_options(self) -> WorkflowStateOptions:


    return WorkflowStateOptions(
        # customize the backoff retry policy for sending email API
        # by default it will retry forever
        # in case of wrong API key, we want to stop it after a minute
        execute_api_retry_policy=RetryPolicy(
            maximum_attempts_duration_seconds=60,
        )
    )
```

#### LLM Prompt and using OpenAI Response API

## Some Key Benefits of the Architecture

## Summary