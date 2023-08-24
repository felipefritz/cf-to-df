# INSTALATION:

1. Create  and activate new virtual environment
    1. python -m venv venv
    2. Activate environment with source venv/bin/activate

2. Install dependencies
    1. pip install -r requirements.txt



# AUTH
Add the uppercase variables as a environment variables to the project
### Contentful:
    1. CONTENTFUL_DELIVERY_API_KEY
    2. CONTENTFUL_SPACE_ID - access token
    3. environment: default='master'
   
### DialogFlow:
1. DIALOGFLOW_AGENT_NAME
2. DIALOGFLOW_CREDENTIALS_PATH: credentials file.json path
3. DIALOGFLOW_AGENT_ID
4. DIALOGFLOW_PROJECT_ID
5. DIALOGFLOW_LOCATION: project location such as us-central1

### Run:
Exeute: python cf-to-df.py

### Logs:
1. The logs will be added to logs file, 1 file for each type of log such as debug, info, warning, error

# TESTS
1. Execute : pytest tests
