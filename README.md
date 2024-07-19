
# QnA_RAG_Agent

This repository demonstrates how a Retrieval-Augmented Generation (RAG) system operates.

## Environment
- **Python Version**: 3.8

## Installation
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
The `QnA_agent_app.py` script is a Flask-based service designed to:
1. Accept a PDF document, a list of questions, an OpenAI API key, and a Slack token as inputs.
2. Utilize OpenAI to answer the questions.
3. Post the answers on the Slack channel associated with the provided Slack token.

### Running the Service
To start the service, run:
```bash
python QnA_agent_app.py
```

### Inputs
- **PDF Document**: The document containing the content to be analyzed.
- **List of Questions**: Questions to be answered based on the PDF content.
- **OpenAI API Key**: Required for accessing OpenAI's services.
- **Slack Token**: Required for posting answers to a Slack channel.

### Sending a Request
You can use the `send_request.py` script to send a request to the service. Run:
```bash
python send_request.py
```

