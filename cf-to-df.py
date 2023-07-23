from services.migration_service import IntentMigrationService
from services.dialogflow import DialogflowService
from settings import *



df = DialogflowService(DIALOGFLOW_PROJECT_ID, DIALOGFLOW_CREDENTIALS_PATH)
agent = df.get_agent_name()
intent_migration_service = IntentMigrationService(CONTENTFUL_SPACE_ID,
                                                  CONTENTFUL_ACCESS_TOKEN,
                                                  DIALOGFLOW_PROJECT_ID, 
                                                  DIALOGFLOW_CREDENTIALS_PATH)
intent_migration_service.migrate_intents()