from abc import ABC, abstractmethod

from google.cloud.dialogflowcx_v3beta1.types.response_message import ResponseMessage
from google.cloud.dialogflowcx_v3beta1.types.page import Page
from google.protobuf import field_mask_pb2 as field_mask
from google.cloud import  dialogflowcx_v3beta1 as dialogflowcx
from google.oauth2 import service_account

from loggers.logger import get_logger
from utils.utils_dialogflow import clean_display_name


logger = get_logger()


def exception_handler_for_exists_objects(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # name = kwargs.get('name', 'Unknown')  # Suponiendo que 'name' es un argumento clave de la función decorada
            if "already exists" in str(e):
                logger.warning(f"object already exists. Continuing...")
            else:
                logger.error(f"An unexpected error occurred : {e}")
                return False
    return wrapper


class AbstractDialogFlowClient(ABC):

    @abstractmethod
    def get_agents_client(self):
        pass
    
    @abstractmethod
    def get_entity_types_client(self):
        pass
    
    @abstractmethod
    def get_fulfillments_client(self):
        pass 
    
    @abstractmethod
    def get_intents_client(self):
        pass
    

class DialogFlowCXClientFactory(AbstractDialogFlowClient):

    def __init__(self, project_id, key_file, location='us-central1'):
        self.project_id = project_id
        self.location = location
        self.credentials = service_account.Credentials.from_service_account_file(key_file)
        self.client_options = {"api_endpoint": f"{self.location}-dialogflow.googleapis.com"}
        self.base_parent = f'projects/{self.project_id}/locations/{self.location}'

    def get_agents_client(self):
        return dialogflowcx.AgentsClient(credentials=self.credentials, client_options=self.client_options)

    def get_entity_types_client(self):
        return dialogflowcx.EntityTypesClient(credentials=self.credentials, client_options=self.client_options)
    
    def get_fulfillments_client(self):
        return dialogflowcx.FulfillmentsClient(credentials=self.credentials, client_options=self.client_options)
   
    def get_flows_client(self):
       return dialogflowcx.FlowsClient(credentials=self.credentials, client_options=self.client_options)

    def get_intents_client(self):
        return dialogflowcx.IntentsClient(credentials=self.credentials, client_options=self.client_options)
    
    def get_pages_client(self):
        return dialogflowcx.PagesClient(credentials=self.credentials, client_options=self.client_options)

    def get_security_settings_client(self):
        return dialogflowcx.SecuritySettingsClient(credentials=self.credentials, client_options=self.client_options)
    
    def get_transition_route_client(self):
        return dialogflowcx.TransitionRouteGroupsClient(
            credentials=self.credentials, client_options=self.client_options)
        
    def get_agent_parent(self, agent_id):
        return self.base_parent + f'/agents/{agent_id}'

    def get_flow_parent(self, agent_id, flow_id):
        return self.get_agent_parent(agent_id) + f'/flows/{flow_id}'

    def get_transition_group_parent(self, agent_id, flow_id):
        return self.get_flow_parent(agent_id, flow_id) + f'/transitionRouteGroups/'
    
    
class AgentManager:
    
    def __init__(self, dialogflow_factory, agent_name):
        self.dialogflow_factory = dialogflow_factory
        self.client = dialogflow_factory.get_agents_client()
        self.agent_id = self._get_agentId_by_name(agent_name)
        self.parent = dialogflow_factory.get_agent_parent(self.agent_id)

    def _get_agentId_by_name(self, agent_name):
        request = dialogflowcx.ListAgentsRequest(parent=self.dialogflow_factory.base_parent)
        try:
            agents = self.client.list_agents(request=request)
            for agent in agents:
                if agent.display_name == agent_name:
                    self.agent = agent
                    agent_id = agent.name.split('/')[-1]
                    return agent_id
        except Exception as e:
            logger.error(f'Error getting agent by name: {e}')
            raise Exception(f'Error getting agent by name: {e}')
        return None


class EntityTypeManager:
    
    def __init__(self, dialogflow_factory, agent_id):
        self.client = dialogflow_factory.get_entity_types_client()
        self.parent = dialogflow_factory.get_agent_parent(agent_id)
        
    def get_entity_type_by_display_name(self, display_name):
        
        request = dialogflowcx.ListEntityTypesRequest(parent=self.parent)
        entity_types = self.client.list_entity_types(request=request)
        for entity_type in entity_types:
            if entity_type.display_name == display_name:
                return entity_type
        return None

    def create_or_update_entity_type(self, display_name, entities_with_synonyms):
        entities = []
        display_name = clean_display_name(display_name.replace(' ', '-'))
        for entity in entities_with_synonyms:
            value = entity['entityValue']
            synonyms = entity.get('synonyms', [value])
            entities.append(dialogflowcx.EntityType.Entity(value=value, synonyms=synonyms))

        existing_entity_type = self.get_entity_type_by_display_name(display_name)
        if existing_entity_type:
            logger.info(f"Updating existing entity type: {display_name}")
            entity_type = self.update_entity_type(existing_entity_type, entities)
        else:
            logger.info(f"Creating entity type {display_name}")
            entity_type = dialogflowcx.EntityType(
                display_name=display_name,
                entities=entities,
                kind=dialogflowcx.EntityType.Kind.KIND_MAP,
                enable_fuzzy_extraction=True,
            )
            entity_type = self.client.create_entity_type(parent=self.parent, entity_type=entity_type)
        return entity_type
    
    def update_entity_type(self, existing_entity_type, entities):
        existing_entity_type.entities = entities
        update_mask = field_mask.FieldMask(paths=["entities"])
        request = dialogflowcx.UpdateEntityTypeRequest(
            entity_type=existing_entity_type,
            update_mask=update_mask
        )
        return self.client.update_entity_type(request=request)
    
    
class FlowManager:
    
    def __init__(self, dialogflow_factory, agent_manager):
        self.dialogflow_factory = dialogflow_factory
        self.agent_parent = agent_manager.parent
        self.client = dialogflow_factory.get_flows_client()
        self.default_flow_id = self.get_default_flow_id()
        self.parent = dialogflow_factory.get_flow_parent(agent_manager.agent_id, self.default_flow_id)

    def get_default_flow_id(self):
        try:
            # Listar todos los flujos en el agente
            request = dialogflowcx.ListFlowsRequest(parent=self.agent_parent) 
            flows = self.client.list_flows(request=request)

            # Buscar el flujo por defecto (si existe)
            for flow in flows:
                if flow.transition_routes:
                    flow_id = flow.name.split('/')[-1]
                    return flow_id
        except Exception as e:
            logger.error(f'Error getting agent by name: {e}')
            raise Exception(f'Error getting agent by name: {e}')
        return None


class TransitionRouteManager:
    
    def __init__(self, dialogflow_factory, flow_client, parent_flow):
        self.client = dialogflow_factory.get_transition_route_client()
        self.flow_client = flow_client
        self.parent_flow = parent_flow
        
    def add_transition_route_to_flow(self, page, intent_name):
        """add the new transition route to the flow that allows to page, this will connect the pages to the flow instead of pages
        So all the pages created will be asociated to the flow.
        
        :page :  The dialog flow page instance
        :intent: name that allows to the page
        """
        flow = self.flow_client.get_flow(name=self.parent_flow)
        transition_route = dialogflowcx.TransitionRoute(
            intent=intent_name,
            target_page=page.name
        )
        
        # Verificar si la transition_route ya existe en el flujo
        if not any(route.intent == transition_route.intent for route in flow.transition_routes):
            flow.transition_routes.append(transition_route)
            # update the flow to the new transition
            update_mask = field_mask.FieldMask(paths=["transition_routes"])
            request = dialogflowcx.UpdateFlowRequest(
                flow=flow,
                update_mask=update_mask
            )
            updated_flow = self.flow_client.update_flow(request=request)
            return updated_flow
    

class PageManager:
    
    def __init__(self, dialogflow_factory, agent_id, flow_id, transition_route_manager):
        self.client = dialogflow_factory.get_pages_client()
        self.parent_flow = f"{dialogflow_factory.get_agent_parent(agent_id)}/flows/{flow_id}"
        self.flow_client = dialogflow_factory.get_flows_client()
        self.transition_route_manager = transition_route_manager

    def get_page_by_display_name(self, display_name):
        request = dialogflowcx.ListPagesRequest(parent=self.parent_flow)
        response = self.client.list_pages(request=request)
        for page in response:
            if page.display_name == display_name:
                return page
        return None
        
    def create_or_update_page_faq(self, intent, response_text):
        # check transition route to verify the intent y and send the response
        agent_response = dialogflowcx.ResponseMessage(text=dialogflowcx.ResponseMessage.Text(text=[response_text]))
        transition_route = dialogflowcx.TransitionRoute(
            intent=intent['parent'],
            trigger_fulfillment=dialogflowcx.Fulfillment(
                messages=[agent_response]  # agent response should be a list
            )
        )

        existing_page = self.get_page_by_display_name(intent['key'])
        if existing_page:
            logger.info(f"page {intent['key']} already exists, updating... ")
            if not any(route.intent == transition_route.intent for route in existing_page.transition_routes):
                existing_page.transition_routes.append(transition_route)
                page = self.update_page(existing_page, intent, transition_route)
            else:
                page = existing_page
        else:
            logger.info(f"Creating page {intent['key']}...")
            page = dialogflowcx.Page(
                display_name=intent['key'],
                transition_routes=[transition_route] # : associate the transition route with the page instead flow
            )
            page = self.client.create_page(parent=self.parent_flow, page=page)
            logger.info(f"Page {intent['key']} created... ")

        self.transition_route_manager.add_transition_route_to_flow(page, intent_name=intent['parent'])
        return page

    def update_page(self, page, intent, transition_route):
        logger.info(f"Page {intent['key']} already exists. Updating...")
        page.transition_routes.append(transition_route)
        update_mask = field_mask.FieldMask(paths=["transition_routes"])
        request = dialogflowcx.UpdatePageRequest(
                page=page,
                update_mask=update_mask
            )
        updated_page = self.client.update_page(request=request)
        return updated_page

    def remove_references_to_page(self, target_page_name):
        # 1. Eliminar referencias de otras páginas
        pages = self.client.list_pages(parent=self.parent_flow)
        for page in pages:
            modified = False
            for route in page.transition_routes:
                if route.target_page == target_page_name:
                    page.transition_routes.remove(route)
                    modified = True
            if modified:
                self.client.update_page(page=page)

        # 2. Eliminar referencias a nivel de flujo
        flow = self.flow_client.get_flow(name=self.parent_flow)
        modified = False
        for route in flow.transition_routes:
            if route.target_page == target_page_name:
                flow.transition_routes.remove(route)
                modified = True
        if modified:
            self.flow_client.update_flow(flow=flow)
    
    def delete_page(self, page_name, max_retries=3, delay=3):
        import time
        self.remove_references_to_page(page_name)
        
        for attempt in range(max_retries):
            try:
                self.client.delete_page(name=page_name)
                logger.info(f"Deleted page: {page_name}")
                return
            except Exception as e:
                logger.warning(f"Failed to delete page {page_name} on attempt {attempt + 1}. Reason: {e}")
                if attempt < max_retries - 1:  # No esperar después del último intento
                    time.sleep(delay)
        print(f"Failed to delete page {page_name} after {max_retries} attempts.")
    
    def delete_all_pages(self):
        pages = self.client.list_pages(parent=self.parent_flow)
        for page in pages:
            self.remove_references_to_page(page.name)
            self.delete_page(page_name=page.name)

    def create_page_from_flow(self, flow):
        page_name = flow["intent"]
        start_node = flow["startNode"]
        entry_text = start_node["text"]

        # Crear la página principal
        master_page = self.create_page(
            display_name=flow['intent'],
            intent_parent=flow['parent'],
            response_text=entry_text, # Usar entry_text aquí
            fallback_text=flow['startNode']['fallbacks'][0]['text'],
            chips=[chip['text'] for chip in flow['startNode']['chips']]
        )

        for chip in start_node["chips"]:
            if 'location' not in chip:
                self.chips_to_payload_response([chip])
            else:
                subpage_display_name = flow['intent'] + chip['text']
                subpage_response_text = chip['location']['text']
                subpage_fallback = chip['location']['fallbacks'][0]['text']

                # Obtener los chips para sub-subpáginas, si existen
                sub_subpage_chips = [sub_chip['text'] for sub_chip in chip['location'].get('chips', [])]

                self.create_page(
                    display_name=subpage_display_name,
                    intent_parent=flow['parent'],
                    response_text=subpage_response_text,
                    fallback_text=subpage_fallback,
                    chips=sub_subpage_chips
                )

                # Crear sub-subpáginas si existen chips para ellas
                if 'chips' in chip['location']:
                    for sub_chip in chip['location']['chips']:
                        if 'url' in sub_chip:
                            # Crear una página con respuesta de tipo payload
                            self.create_payload_page(flow, chip)
                        else:
                            self.create_page_from_flow(sub_chip)


    def create_page(self, display_name, intent_parent, response_text, fallback_text, chips=None):
        text_response = ResponseMessage(
            text={
                'text': [response_text]
            }
        )
        payload = {
            # Define más atributos del payload si es necesario.
            'chips': chips if chips else []
        }
        payload_response = ResponseMessage(
            payload=payload
        )
        page = Page(
            display_name=display_name,
            entry_fulfillment={
                'messages': [text_response, payload_response]
            },
            transition_routes=[
                {
                    'intent': intent_parent,  # Utiliza el nombre de la página como intención.
                    'trigger_fulfillment': {
                        'messages': [ResponseMessage(
                            text={'text': [fallback_text]}
                        )]
                    }
                }
            ]
        )
        try:
            response = self.client.create_page(parent=self.parent_flow, page=page)
            return response
        except Exception as e:
            logger.warning(f'page {display_name} already exists')
            return False

    
    def chips_to_payload_response(self, chips):
        return {"richContent": [{"options": chips, "type": "chips"}]}

    def create_payload_page(self, flow, chip):
        # Generar el nombre de la página usando el 'intent' del flow y el 'text' o 'entityValue' del chip
        if "entityValue" in chip:
            page_name = flow["intent"] + "." + chip["entityValue"]["entityValue"]
        else:
            page_name = flow["intent"] + "." + chip["text"]
        
        payload_response = ResponseMessage(
            payload={
                'url': chip['url']
            }
        )
        page = Page(
            display_name=page_name,
            entry_fulfillment={
                'messages': [payload_response]
            }
        )
        try:
            response = self.client.create_page(parent=self.parent_flow, page=page)
            return response
        except Exception as e:
            logger.warning(f'page {page_name} already exists')
            return False



class IntentManager:
    
    def __init__(self, dialogflow_factory, agent_id):
        self.client = dialogflow_factory.get_intents_client()
        self.parent = dialogflow_factory.get_agent_parent(agent_id)

    def create_intent_if_not_exists(self, display_name: str, training_phrase: str) -> dialogflowcx.Intent:

        """
        Create an intent if it doesn't exist
        :param display_name: name of the intent 
        :param training_phrase:  Is the question in the flow from contentful 
        :return: dialogflowcx.Intent
        
        """
        intent = dialogflowcx.Intent()
        part = dialogflowcx.Intent.TrainingPhrase.Part(text=training_phrase)
        training_phrase_obj = dialogflowcx.Intent.TrainingPhrase(parts=[part], repeat_count=1)

        intent.display_name = display_name
        intent.training_phrases = [training_phrase_obj]
        request = dialogflowcx.CreateIntentRequest(
        parent=self.parent,
        intent=intent,
    )
        try:
            response = self.client.create_intent(request=request)
            logger.info(f"Intent created: {display_name}")
            return response
        except Exception as e:
            if "already exists" in str(e):
                logger.warning(f"Intent with display name '{display_name}' already exists. Continuing...")
            else:
                logger.error(f"An unexpected error occurred while creating intent {display_name}: {e}")
                return False
 
    def get_intents_all(self):
        """
        get all intents for the current agent
        :return: list of dicts with the following structure: 
        
        [{display_name: flow.example.info, parent:
        'projects/project_id/locations/location_id/agent/agent_id/intents/intent_id}, etc...]
        """
        intents = self.client.list_intents(request={"parent": self.parent})
        intents_list = [{'display_name': intent.display_name, 'parent': intent.name} for intent in intents]
        return intents_list
