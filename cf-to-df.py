import os
from services.contentful_service import ContentfulService
from clients.contentful_client import ContentfulClient
from clients.dialogflow_client import DialogFlowCXClientFactory
from services.dialogflow_service import  DialogflowServiceCX


if __name__ == '__main__':
    CONTENTFUL_DELIVERY_API_KEY = os.getenv('CONTENTFUL_DELIVERY_API_KEY')
    CONTENTFUL_SPACE_ID = os.getenv('CONTENTFUL_SPACE_ID')
    
    DIALOGFLOW_AGENT_NAME = os.getenv('DIALOGFLOW_AGENT_NAME')
    DIALOGFLOW_AGENT_ID = os.getenv('DIALOGFLOW_AGENT_ID')
    DIALOGFLOW_CREDENTIALS_PATH = os.getenv('DIALOGFLOW_CREDENTIALS_PATH')
    DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
    DIALOGFLOW_LOCATION = os.getenv('DIALOGFLOW_LOCATION')

    # 1. contentful connection
    contentful_client = ContentfulClient(space_id=CONTENTFUL_SPACE_ID,
                                         access_token=CONTENTFUL_DELIVERY_API_KEY)
    cf_service = ContentfulService(contentful_client)
    
    # 2. dialogflow connection
    df_client = DialogFlowCXClientFactory(project_id=DIALOGFLOW_PROJECT_ID,
                                          key_file=DIALOGFLOW_CREDENTIALS_PATH,
                                          location=DIALOGFLOW_LOCATION)
    df_service = DialogflowServiceCX(df_client, DIALOGFLOW_AGENT_NAME)

    # 3. Get contentful data
    # 3.1 entity_types: 
    entity_types = cf_service.entity_types
    # 3.2 intents:
    intents = cf_service.intents
    # 3.3 flows: 
    flows = cf_service.flows_with_subpages
    
    # 4. Create or update dialog flow data
    # 4.1 create entity types
    # df_service.create_entity_types(entity_types=entity_types)
    # 4.2 Create intents
    #df_service.create_intents(intents=intents)
    # 4.3 Create flows
    df_service.create_flows(flows_list=flows)
    # 4.4 Create faq. pages 
    # TODO
    # flows_with_faq = [flow for flow in flows if flow['intent'].startswith('faq') if 'intent' in flow]


    


    
    
    
    
