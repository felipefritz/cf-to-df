# services/intent_migration_service.py

from .contentful_service import ContentfulService
from .dialogflow import DialogflowService
from google.cloud import dialogflow


class IntentMigrationService:
    def __init__(self, contentful_space_id, contentful_access_token, dialogflow_project_id, dialogflow_credentials_path):
        self.contentful_service = ContentfulService(contentful_space_id, contentful_access_token)
        self.dialogflow_service = DialogflowService(dialogflow_project_id, dialogflow_credentials_path)

    def migrate_intents(self):
        entries = self.contentful_service.get_entries('intent')

        for entry in entries:
            intent = dialogflow.Intent(
                display_name=entry.fields()['name'],
                training_phrases=[
                    dialogflow.Intent.TrainingPhrase(parts=[dialogflow.Intent.TrainingPhrase.Part(text=phrase)])
                    for phrase in entry.fields()['training_phrases']
                ],
                messages=[
                    dialogflow.Intent.Message(text=dialogflow.Intent.Message.Text(text=[message]))
                    for message in entry.fields()['messages']
                ]
            )

            self.dialogflow_service.create_intent(intent)
