## How to run

## How to Run

To run the `main.py` script located in the `ai-agent-email` directory, follow the steps below:

### Prerequisites

Make sure you have the following installed and set up:

1. [Python 3.13.2](https://www.python.org/downloads/)
2. [Poetry](https://python-poetry.org/docs/) for dependency management and virtual environments.
3. All required environment variables.

### Environment Variables

Before running the script, ensure the following environment variables are properly configured in your system:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `GOOGLE_EMAIL_ADDRESS`: The email address you'll use for sending emails.
- `GOOGLE_EMAIL_APP_PASSWORD`: The application password for your Google account.

You can set these variables in your shell profile file (e.g., `.bashrc`, `.zshrc`, etc.) or export them before running
the script:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export GOOGLE_EMAIL_ADDRESS="your-email-address"
export GOOGLE_EMAIL_APP_PASSWORD="your-app-password"
```

### Install Dependencies

Once Poetry is installed, navigate to the project directory and install the required dependencies by running:

```bash
poetry install
```

This will create a virtual environment and install all necessary packages listed in the `pyproject.toml` file.

### Run the Script

To start the script, execute the following command:

```bash
poetry run python ai-agent-email/main.py
```

This will launch the `main.py` script using Poetry's virtual environment.
