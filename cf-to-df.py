import os

from services.migration_service import IntentMigrationService
from services.contentful_service import ContentfulService
from services.dialogflow import DialogflowService
from settings import *


if __name__ == '__main__':
    contentful_space_id = os.getenv('CONTENTFUL_SPACE_ID')
    contentful_api_key = os.getenv('CONTENTFUL_delivery_API_KEY')
    cf_service = ContentfulService(contentful_space_id, contentful_api_key)
    cf_service.get_all_entries()
    content_type_names = cf_service.get_content_type_names()
    data = cf_service.extract_values_from_all_entries(cf_service.all_entries, export_to_excel=True)


    flow_df = data['flow']
    entityType_df = data['entityType']