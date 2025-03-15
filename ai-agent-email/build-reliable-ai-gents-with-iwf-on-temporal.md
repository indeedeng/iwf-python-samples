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

#### InitState

#### AgentState

#### ScheduleState

#### SendingState

## Comparison with some alternatives

## Summary