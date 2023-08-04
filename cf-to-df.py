import os

from services.contentful_service import ContentfulService
from clients.contentful_client import ContentfulClient
from clients.dialogflow_client import DialogFlowCXClientFactory
from services.dialogflow_service import DialogflowService, DialogflowServiceCX


if __name__ == '__main__':
    contentful_space_id = os.getenv('CONTENTFUL_SPACE_ID')
    contentful_api_key = os.getenv('CONTENTFUL_DELIVERY_API_KEY')
    dialog_flow_agent_name = os.getenv('DIALOG_FLOW_AGENT_NAME')


    # clients
    df_client = DialogFlowCXClientFactory(project_id='scotiabank-393322', key_file='df-credentials.json')
    contentful_client = ContentfulClient(contentful_space_id, contentful_api_key)


    # services
    cf_service = ContentfulService(contentful_client)
    df_service = DialogflowServiceCX(df_client, dialog_flow_agent_name)


     # run contentful service
    cf_service.get_all_entries()
    content_type_names = cf_service.get_content_type_names()
    contentful_data = cf_service.extract_values_from_all_entries(cf_service.all_entries, export_to_excel=True)
    
    flows_df = contentful_data['flow'].to_dict('records')
    entity_types = contentful_data['entityType'].to_dict('records')
    
    # df_service.create_intents(intents=flows_df)

    for entity_type in entity_types:
        df_service.create_entity_type(display_name=entity_type.get('entityType'),
                                      entities_with_synonyms=entity_type['entityValue'])
    
    intents = df_service.get_intents_all()
        
