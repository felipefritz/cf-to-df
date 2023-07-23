from google.cloud import dialogflow
from google.auth import exceptions
from google.oauth2 import service_account

class DialogflowService:
    def __init__(self, project_id, credentials_path):
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.agents_client = dialogflow.AgentsClient(credentials=credentials)
            self.parent = f'projects/{project_id}'
        except exceptions.DefaultCredentialsError:
            print("Error al cargar las credenciales. Verifica que tu archivo de credenciales esté configurado correctamente.")
    
    def get_agent(self):
        return self.agents_client.get_agent(self.parent)


