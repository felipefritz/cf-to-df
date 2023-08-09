import os

from services.contentful_service import ContentfulService
from clients.contentful_client import ContentfulClient
from clients.dialogflow_client import DialogFlowCXClientFactory
from services.dialogflow_service import  DialogflowServiceCX


if __name__ == '__main__':
    contentful_space_id = os.getenv('CONTENTFUL_SPACE_ID')
    contentful_api_key = os.getenv('CONTENTFUL_DELIVERY_API_KEY')
    dialog_flow_agent_name = os.getenv('DIALOG_FLOW_AGENT_NAME')

    # 1. contentful connection
    contentful_client = ContentfulClient(contentful_space_id, contentful_api_key)
    cf_service = ContentfulService(contentful_client)
    flows = cf_service.flows
    entity_types = cf_service.entity_types

    # 2. dialogflow connection
    df_client = DialogFlowCXClientFactory(project_id='scotiabank-393322', key_file='df-credentials.json')
    df_service = DialogflowServiceCX(df_client, dialog_flow_agent_name)

    # 3. process data
    flows_with_faq = [flow for flow in flows if flow['intent'].startswith('faq')]
                    
    # 4. dialog flow create or update data
    df_service.create_intents(flows=flows)
    df_service.create_entity_types(entity_types)
    df_service.create_pages_faq(flows_with_faq)
    df_service.delete_pages()
    
    
    
    
    
    
    
