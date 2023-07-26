# services/intent_migration_service.py

from .contentful_service import ContentfulService
from .dialogflow import DialogflowService
from google.cloud import dialogflow


class IntentMigrationService:
    def __init__(self, contentful_space_id, contentful_access_token, dialogflow_project_id, dialogflow_credentials_path):
        self.contentful_service = ContentfulService(contentful_space_id, contentful_access_token)
        self.dialogflow_service = DialogflowService(dialogflow_project_id, dialogflow_credentials_path)

    def migrate_intents(self):
        entries = self.contentful_service.get_all_entries()
        # TODO: This should get all intents from the contentful entries
