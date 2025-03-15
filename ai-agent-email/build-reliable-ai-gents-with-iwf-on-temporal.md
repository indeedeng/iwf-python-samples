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

## Dive deep into implementation

## Comparison with some alternatives

## Summary