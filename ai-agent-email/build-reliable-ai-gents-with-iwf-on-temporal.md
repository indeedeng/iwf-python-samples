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

See more in iWF [persistence](https://github.com/indeedeng/iwf/wiki/Persistence) documentation.

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
configures [special execution parameters](https://github.com/indeedeng/iwf/wiki/WorkflowStateOptions#workflowstate-waituntilexecute-api-timeout-and-retry-policy)
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

The SendingState represents the final step in the email workflow, handling the actual delivery of the
composed email through SMTP integration with Gmail.
This state demonstrates iWF's robust error handling capabilities through its custom retry policy configuration.
When executing, it connects to Gmail's SMTP server, authenticates using the previously validated credentials,
constructs the email message with the subject and body from persisted workflow data,
and sends it to the recipient.

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

What makes this state particularly reliable is its error handling approach. The `get_state_options` method
applies
a [custom retry policy](https://github.com/indeedeng/iwf/wiki/WorkflowStateOptions#workflowstate-waituntilexecute-api-timeout-and-retry-policy)
that limits retry attempts to 60 seconds, preventing indefinite retries
in case of permanent failures like invalid credentials. This balance between persistence
(automatically retrying transient errors) and pragmatism (giving up after a reasonable time for permanent errors)
is essential for production systems that interact with external services.

After successful email delivery, the workflow's status is updated to "sent" and the workflow gracefully completes,
having fulfilled its purpose of composing, scheduling, and delivering an email based on the user's requirements.

#### LLM Prompt and OpenAI Response API

```python
def process_user_request(req: str, persistence: Persistence) -> AgentResponse:
    response = do_process_user_request(req, persistence.get_data_attribute(DA_PREVIOUS_RESPONSE_ID))
    if isinstance(response.id, str):
        persistence.set_data_attribute(DA_PREVIOUS_RESPONSE_ID, response.id)

    resp = response.output[0].content[0].text
    return AgentResponse.model_validate_json(resp)


def do_process_user_request(req: str, previous_response_id: str | None):
    client = OpenAI()

    current_timestamp = int(time.time())
    response = client.responses.create(
        model="gpt-4o",
        instructions=f"""
        Help prepare an email to be sent. Based on user requests, return email's subject, body, recipient 
        , sending time and/or cancel_operation, if any of them available. 
        The email subject or body may need to be translated if user requests to.
        The email subject and body must be complete, do not leave any place holders like [Your Name]. 
        The email's recipient should be in a valid email format, other wise, return empty string for that field.
        The sending time must be in unix timestamp in seconds. 
        The current timestamp is {current_timestamp}.
        User may use relative time description based on today/now, you should calculate the timestamp based on the current timestamp {current_timestamp}. 
        For example, tomorrow means current timestamp plus 86400, 
        X seconds later means {current_timestamp} + X, 
        X minutes later means {current_timestamp} + X*60, 
        X hours later means {current_timestamp} + X * 3600.
        MAKE SURE the sending time is ALWAYS greater than the above provided current timestamp, if NOT, then it's wrong, you should always use current timestamp as the base. 
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
```

The AI Agent Email workflow leverages
OpenAI's [new Responses API](https://community.openai.com/t/introducing-the-responses-api/1140929),
a powerful capability released in March 2025 (a few days ago as this blogpost) that enables stateful conversations
by persisting conversation history on OpenAI's servers. This integration showcases a perfect synergy
between iWF's workflow durability and OpenAI's conversation persistence.

At the core of this implementation is the `process_user_request` function, which serves as the bridge between the
workflow and OpenAI's language model. Here's how it works:

1. **Stateful Conversation Management**: The function reads the previously stored `previous_response_id` from iWF's
   durable persistence layer (via `persistence.get_data_attribute(DA_PREVIOUS_RESPONSE_ID)`) and passes it to the OpenAI
   API call.

2. **Response ID Persistence**: After receiving a response from OpenAI, the function extracts the new response ID (
   `response.id`) and stores it back in the workflow's persistence layer, ensuring conversation continuity across
   interactions.

3. **Structured Output Format**: The implementation uses OpenAI's structured response capabilities (
   `text=Converter.get_response_format(AgentOutputSchema(AgentResponse))`) to ensure the AI generates responses in a
   consistent JSON format that maps directly to the `AgentResponse` model.
   The AgentOutputSchema and Converter are from OpenAI's agents SDK, which also supports Response API already,
   but doesn't allow passing a responseID yet.

4. **Detailed Instructions with Real-Time Context**: The prompt provides comprehensive guidance to the model, covering
   email composition,
   translation, and cancellation handling. Crucially, it injects the current timestamp (
   `current_timestamp = int(time.time())`)
   multiple times throughout the prompt to ensure accurate time calculations, overriding the model's tendency to use
   outdated
   timestamps from its training data. This technique is essential for scheduling functionality, as it enables precise
   relative
   time expressions like "tomorrow" or "in 2 hours" to be correctly converted to absolute Unix timestamps.

## Summary of Key Benefits of the Architecture

The AI Agent Email architecture showcases a remarkable balance between simplicity of design and implementation,
and extraordinary power and resilience. What makes iWF on Temporal particularly suited for AI agent development
is the elegant, straightforward code that belies its enterprise-grade capabilities.

### Simplicity of Software Design and Implementation

Despite providing robust reliability features, the codebase remains remarkably clean and straightforward:

- **Declarative State Machine**: The workflow is defined as a simple state machine with four clear states, each with
  specific responsibilities
- **Minimal Boilerplate**: The framework handles the complex orchestration details, allowing developers to focus purely
  on business logic
- **Clear Separation of Concerns**: Each state (Init, Agent, Schedule, Sending) encapsulates specific functionality,
  making the code easier to understand and maintain
- **Intuitive APIs**: The RPC interfaces provide a clean boundary for external systems to interact with the workflow

### Powerful Production-Grade Capabilities

Beyond this simplicity, the architecture provides exceptional power and reliability:

1. **Checkpoint & Recovery**: Each state execution is automatically persisted in iWF server and Temporal, enabling
   seamless resumption after any type of failure without losing progress. This creates natural resilience against
   instance crashes, network failures, or even entire zone outages.

2. **Complete History for Debugging**: The input and output of each state execution is automatically persisted and
   visible in the Temporal WebUI, providing invaluable data for troubleshooting production issues, understanding
   execution patterns, and auditing workflow actions.

3. **Rich Operational Tooling**: iWF and Temporal provide numerous built-in tools that would otherwise require extensive
   custom development:
    - Reset workflow execution like a time machine to any previous point
    - Skip timers for testing or operational interventions
    - Advanced workflow search capabilities across multiple dimensions
    - Comprehensive monitoring and observability
    - Intuitive Web UI for debugging workflows in real-time, watching execution progress, and inspecting detailed error
      stack traces

4. **Simplified Versioning**: iWF's architecture eliminates the notorious "Non-Deterministic errors" common in
   replay-based workflow frameworks, making versioning and updates remarkably straightforward. Developers can deploy new
   workflow versions without complex code rewrites.

5. **No "Continue-as-New" Complexity**: The platform handles workflow history truncation and long-running execution
   behind the scenes, removing the need for developers to implement complex "continue-as-new" patterns found in other
   frameworks.

6. **Unmatched Scalability and Reliability**: The entire application runs as a distributed system that can scale to
   support billions of concurrent workflows and recover automatically from any instance or network failure.

### Perfect for AI Agent Architectures

This combination of simplicity and power makes iWF on Temporal an ideal foundation for AI agent applications, which have
unique requirements for both durability and flexibility. The architecture enables:

- **Stateful Conversation Persistence**: Combined workflow state and conversation context across system boundaries
- **Long-Running Operations**: Support for operations that span hours, days, or weeks without complexity
- **External API Resilience**: Built-in retry policies that handle transient failures intelligently
- **User Interruption Patterns**: Natural handling of asynchronous user interactions and cancellations
- **Reliable Scheduling**: Rock-solid support for time-based operations with durable timers

By leveraging iWF on Temporal, developers can build sophisticated AI agents with code that remains clear, concise, and
maintainable while benefiting from enterprise-grade reliability, scalability, and operational capabilities.

### Additional Architectural Advantages

Beyond what we've demonstrated in this example, iWF provides several more powerful capabilities that further
enhance its suitability for AI agent development:

1. **REST API-Based Communication**: The iWF SDK and server communicate via standard REST APIs, offering
   significant operational benefits:
    - Easier to monitor with standard HTTP monitoring tools
    - Simpler to debug with common HTTP tracing and logging methods
    - More observable with consistent request/response patterns
    - Compatible with existing API management tools and proxies
    - Better network transparency and troubleshooting

2. **Massive Parallel State Execution**: While not showcased in this example, iWF supports executing
   multiple state instances in parallel:
    - Can run hundreds of state executions concurrently within a single workflow
    - Enables complex parallel processing pipelines for data-intensive operations
    - Supports sophisticated fan-out/fan-in patterns for distributed processing
    - Maintains all durability guarantees even with massive parallelism
    - Perfect for coordinating multiple AI models or data sources simultaneously

3. **Highly Testable Workflow Architecture**: The design philosophy prioritizes testability:
    - All iWF SDK interfaces can be easily mocked for comprehensive unit testing
    - Workflow logic can be verified independently of the underlying infrastructure
    - State transitions can be tested in isolation with dependency injection
    - End-to-end testing requires minimal infrastructure setup
    - Test coverage is easier to achieve with clear state boundaries

4. **True Workflow-as-Code Paradigm**: Unlike DSL-based alternatives, everything is defined as standard code:
    - Enables higher-level abstractions and patterns across workflows
    - Promotes code reusability through standard software engineering practices
    - Fully supports DRY principles and other software design patterns
    - Integrates seamlessly with existing development tools and processes
    - Allows workflows to be treated as first-class software artifacts

These additional capabilities further cement iWF on Temporal as the ideal platform for building AI agents
that need to be reliable, scalable, and maintainable in production environments.

Beyond these, there are even more powerful features that aren't demonstrated in this example but can be invaluable for
complex use cases:

1. **State API Failure Handling/Recovery After Retries**: While default behavior fails the workflow when state APIs
   exhaust retry attempts, iWF provides
   sophisticated [failure handling mechanisms](https://github.com/indeedeng/iwf/wiki/WorkflowStateOptions#state-api-failure-handlingrecovery-after-retries-are-exhausted)
   that allow workflows to:
    - Implement SAGA compensation patterns after retries are exhausted
    - Execute clean-up logic to maintain system consistency
    - Take alternative paths when operations persistently fail
    - Preserve partial progress despite subsystem failures

2. **Wait For State Completion**:
   The [wait-for-state-completion](https://github.com/indeedeng/iwf/wiki/How-to-wait-for-a-workflow-state-to-complete)
   feature enables frontend clients to:
    - Wait synchronously for specific background actions to complete
    - Build complex interaction logic with real-time feedback
    - Implement progressive user experiences with background processing
    - Coordinate between user actions and system state changes

3. **RPC Locking**: iWF provides
   sophisticated [RPC locking mechanisms](https://github.com/indeedeng/iwf/wiki/RPC-locking:-What-does-the-atomicity-of-RPC-really-mean%3F)
   to prevent race conditions:
    - Ensures atomicity of operations across concurrent RPCs and WorkflowStates
    - Prevents data corruption when multiple clients interact with the same workflow
    - Provides configurable locking strategies for different use cases
    - Maintains consistency without requiring developers to implement complex synchronization code
    - Critical for AI agents where multiple users or systems might be interacting with the same workflow

These advanced capabilities allow developers to tackle even the most complex AI agent scenarios with robust error
handling,
sophisticated user interaction patterns, and graceful degradation strategies.
