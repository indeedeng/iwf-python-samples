## How to Run

To run the `main.py` script located in the `ai-agent-email` directory, follow the steps below:

### Prerequisites

Make sure you have the following installed and set up:

1. [Python 3.13.2](https://www.python.org/downloads/)
2. [Poetry](https://python-poetry.org/docs/) for dependency management and virtual environments.
3. [Node.js and npm](https://nodejs.org/) for building the frontend.
4. All required environment variables.

### Environment Variables

Before running the script, ensure the following environment variables are properly configured in your system:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `GOOGLE_EMAIL_ADDRESS`: The email address you'll use for sending emails. E.g. qlong.seattle@gmail.com
- `GOOGLE_EMAIL_APP_PASSWORD`: The application password for your Google account. You can go
  to [Google app password](security.google.com/settings/security/apppasswords) to create a password for your account.

You can set these variables in your shell profile file (e.g., `.bashrc`, `.zshrc`, etc.) or export them before running
the script:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_EMAIL_ADDRESS="your-email-address"
export GOOGLE_EMAIL_APP_PASSWORD="your-app-password"
```

### Backend Setup

Once Poetry is installed, navigate to the project directory and install the required dependencies by running:

```bash
poetry install
```

This will create a virtual environment and install all necessary packages listed in the `pyproject.toml` file.

### Frontend Setup

To set up the React TypeScript frontend:

1. Install the required npm packages:

```bash
cd ai-agent-email
npm install
```

2. Build the frontend:

```bash
npm run build
```

For development, you can use the watch mode:

```bash
npm start
```

### Run the Application

To start the application, execute the following command:

```bash
poetry run python ai-agent-email/main.py
```

This will launch the Flask application at http://localhost:8802. Open your browser and navigate to this URL to access the AI Agent Email interface.

## Using the Application

1. When you first open the application, you'll see a text box and a "Talk to Agent" button.
2. Enter your request in the text box (e.g., "Help me write an email to thank John for his help on the project").
3. Click the "Talk to Agent" button to send your request to the AI agent.
4. The agent will process your request and provide a response that will be displayed on the page.
