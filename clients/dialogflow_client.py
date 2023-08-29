
import time        
from abc import ABC, abstractmethod

from google.oauth2 import service_account

from google.cloud import  dialogflowcx_v3beta1 as dialogflowcx
from google.protobuf import field_mask_pb2 as field_mask

from loggers.logger import get_logger
from utils.utils_dialogflow import DialogFlowUtils


info_logger = get_logger("info")
error_logger = get_logger("error")
debug_logger = get_logger("debug")

    
class DialogFlowCXClientFactory:

    def __init__(self, project_id, key_file, location):
        self.project_id = project_id
        self.key_file = key_file
        self.location = location
        self._credentials = None
        self.client_options = {"api_endpoint": f"{self.location}-dialogflow.googleapis.com"}
        self.base_parent = f'projects/{self.project_id}/locations/{self.location}'
    
    @property
    def credentials(self):
        if self._credentials is None:
            try:
                self._credentials = service_account.Credentials.from_service_account_file(self.key_file)
            except Exception as e:
                error_logger.error("error trying to authenticate dialog flow service: " +str(e))
                return None
        return self._credentials

    def agents_client(self):
        try:
            agent_client = dialogflowcx.AgentsClient(credentials=self.credentials, client_options=self.client_options)
        except Exception as e:
            error_logger.error("error trying to get agents client")
        return agent_client
    
    def flows_client(self):
       return dialogflowcx.FlowsClient(credentials=self.credentials, client_options=self.client_options)

    def entity_types_client(self):
        return dialogflowcx.EntityTypesClient(credentials=self.credentials, client_options=self.client_options)
    
    def intents_client(self):
        return dialogflowcx.IntentsClient(credentials=self.credentials, client_options=self.client_options)
    
    def pages_client(self):
        return dialogflowcx.PagesClient(credentials=self.credentials, client_options=self.client_options)
    
    def transition_route_client(self):
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
        self.client = dialogflow_factory.agents_client()
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
            error_logger.error(f'Error getting agent by name: {e}')
            raise Exception(f'Error getting agent by name: {e}')
        return None


class EntityTypeManager:
    
    def __init__(self, dialogflow_factory, agent_id):
        """ Manage the entity types methods associated with dialogflow.

        Args:
            dialogflow_factory (_type_): The dialogflow factory class with the entity
            type dialog flow client: dialogflowcx.EntityTypesClient
            agent_id (_type_):The agent id associated with the dialog flow client
        """
        self.client = dialogflow_factory.entity_types_client()
        self.parent = dialogflow_factory.get_agent_parent(agent_id)
        
    def _add_synonyms_to_entity_types(self, entity_types: list[dict]):
        """add synonyms from contentful to for each entity type dialog flow object
        Args:
            entity_types (_type_): List of dicts with entity types with keys entityValue and synonyms

        Returns:
            _type_: A list of entity types dialog flow objects
        """
        entities = []
        for entity in entity_types:
            value = entity['entityValue']
            synonyms = entity.get('synonyms', [value])
            entities.append(dialogflowcx.EntityType.Entity(value=value, synonyms=synonyms))
        return entities
        
    def get_entity_type_by_display_name(self, display_name: str):
        """ Retrieves an entity type from Dialog Flow Client by display name.
        Args:
            display_name (_type_): Name of entity type as string.

        Returns:
            _type_: if exists , returns a dialog flow entity type object
        """
        request = dialogflowcx.ListEntityTypesRequest(parent=self.parent)
        entity_types = self.client.list_entity_types(request=request)
        for entity_type in entity_types:
            if entity_type.display_name == display_name:
                return entity_type
        return None
       
    def create_or_update_entity_type(self, display_name: str, entity_types: list[dict]):
        """ Create or update an new entity type in dialog flow by display name and synonyms.
            An entity type has many entities.
        Returns:
            _type_: Dialog flow entity type object
        """
        display_name = DialogFlowUtils.clean_display_name(name=display_name.replace(' ', '-'))
        entities = self._add_synonyms_to_entity_types(entity_types=entity_types)
        existing_entity_type = self.get_entity_type_by_display_name(display_name=display_name)
        
        try:
            if existing_entity_type:
                info_logger.info(f"Updating existing entity type: {display_name}")
                entity_type = self.update_entity_type(existing_entity_type, entities)
            else:
                info_logger.info(f"Creating entity type {display_name}")
                entity_type = dialogflowcx.EntityType(
                    display_name=display_name,
                    entities=entities,
                    kind=dialogflowcx.EntityType.Kind.KIND_MAP,
                    enable_fuzzy_extraction=True,
                )
                entity_type = self.client.create_entity_type(parent=self.parent, entity_type=entity_type)
            return entity_type
        
        except Exception as e:
            if "already exists" in str(e):
                info_logger.warning(f"Entity Type '{display_name}' already exists and nothing to update...")
            else:
                error_logger.error(f"An unexpected error occurred while creating intent {display_name}: {e}")
    
    def update_entity_type(self, existing_entity_type, entities: list):
        """ Update an entity type entities, FieldMask is a gpc method
        that updates objects with the specified fields and objects
        Args:
            existing_entity_type (_type_): Dialog flow entity type object
            entities (_type_): A list of entity dialog flow objects related to the entity type.
        Returns:
            _type_: Entity type object
        """
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
        self.client = dialogflow_factory.flows_client()
        self.default_flow_id = self.get_default_flow_id()
        self.parent = dialogflow_factory.get_flow_parent(agent_manager.agent_id, self.default_flow_id)

    def get_flow_by_display_name(self, display_name):
        try:
            request = dialogflowcx.ListFlowsRequest(parent=self.agent_parent) 
            flows = self.client.list_flows(request=request)

            for flow in flows:
                if flow.display_name == display_name:
                    return flow
        except Exception as e:
            error_logger.error(f'Error getting flow: {e}')
            raise Exception(f'Error getting flow by name: {e}')
        return None
    
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
            error_logger.error(f'Error getting flow: {e}')
            raise Exception(f'Error getting flow: {e}')
        return None

    def create_flow(self, display_name, description=None):
        """
        Crea un nuevo flujo en DialogFlow.

        Args:
        - display_name (str): El nombre del flujo.
        - description (str, opcional): Una descripción para el flujo.

        Returns:
        - flow (dialogflowcx.Flow): El flujo creado.
        """
        try:
            flow = dialogflowcx.Flow(
                display_name=display_name,
                description=description
            )
            request = dialogflowcx.CreateFlowRequest(
                parent=self.agent_parent,
                flow=flow
            )
            flow = self.client.create_flow(request=request)
            return flow
        except Exception as e:
            if "already exists" in str(e):
                error_logger.warning(f"Flow '{display_name}' already exists. Continuing...")
                flow = self.get_flow_by_display_name(display_name)
                return flow
            else:
                error_logger.error(f"An unexpected error occurred while creating intent {display_name}: {e}")
                return flow
        
    def update_flow(self, flow):
        request = dialogflowcx.UpdateFlowRequest(
            flow=flow,
            update_mask=field_mask.FieldMask(paths=["start_flow_page"])
        )
        return self.client.update_flow(request=request)


class IntentManager:
    
    def __init__(self, dialogflow_factory, agent_id):
        self.client = dialogflow_factory.intents_client()
        self.parent = dialogflow_factory.get_agent_parent(agent_id)

    def create_intent_if_not_exists(self, display_name: str, training_phrase: str) -> dialogflowcx.Intent:
        """Create an intent if it doesn't exist, or update if it does.

        Args:
            display_name (str): Name of the intent.
            training_phrase (str): Training phrase to be added.

        Returns:
            dialogflowcx.Intent: Created or updated intent.
        """
        existing_intent = self.get_intent_by_display_name(display_name)

        if existing_intent:
            info_logger.info(f"Intent already exists: {display_name}, updating...")
            # Update the existing intent with new training phrase
            return self.update_intent(existing_intent, training_phrase)

        # If intent does not exist, then create it
        intent = dialogflowcx.Intent()
        part = dialogflowcx.Intent.TrainingPhrase.Part(text=training_phrase)
        training_phrase_obj = dialogflowcx.Intent.TrainingPhrase(parts=[part], repeat_count=1)
        
        intent.display_name = display_name
        intent.training_phrases = [training_phrase_obj]
        request = dialogflowcx.CreateIntentRequest(parent=self.parent, intent=intent)
        try:
            response = self.client.create_intent(request=request)
            info_logger.info(f"Intent created: {display_name}")
            return response
        except Exception as e:
            if "already exists" in str(e):
                info_logger.warning(f"Intent with display name '{display_name}' already exists. Continuing...")
            else:
                error_logger.error(f"An unexpected error occurred while creating intent {display_name}: {e}")
            
    def get_intent_by_display_name(self, display_name):
        """Get intent by its display name.
        
        Args:
            display_name (str): Display name of the intent to fetch.

        Returns:
            Intent if found, else None.
        """
        request = dialogflowcx.ListIntentsRequest(parent=self.parent)
        intents = self.client.list_intents(request)
        for intent in intents:
            if intent.display_name == display_name:
                return intent
        return None
    
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
    
    def update_intent(self, intent, training_phrase):
        """Update intent with new training phrase.
        
        Args:
            intent (dialogflowcx.Intent): Existing intent to be updated.
            training_phrase (str): Training phrase to be added.

        Returns:
            Updated intent.
        """
        part = dialogflowcx.Intent.TrainingPhrase.Part(text=training_phrase)
        training_phrase_obj = dialogflowcx.Intent.TrainingPhrase(parts=[part], repeat_count=1)
        # Ensure all training phrases have a valid repeat_count
        for tp in intent.training_phrases:
            if tp.repeat_count <= 0:
                tp.repeat_count = 1
        intent.training_phrases.append(training_phrase_obj)
        request = dialogflowcx.UpdateIntentRequest(intent=intent)
        
        return self.client.update_intent(request=request)


class PageManager:
    """Manager for handling operations related to Dialogflow Pages."""

    def __init__(self, dialogflow_factory, agent_id, flow_id):
        """Initialize the PageManager.

        Args:
            dialogflow_factory: Factory to provide clients for various Dialogflow operations.
            agent_id: ID of the agent.
            flow_id: ID of the flow.
            transition_route_manager: Manager to handle transition routes.
        """
        self.client = dialogflow_factory.pages_client()
        self.parent_flow = f"{dialogflow_factory.get_agent_parent(agent_id)}/flows/{flow_id}"
        self.flow_client = dialogflow_factory.flows_client()

    def get_page_by_display_name(self, display_name, parent_flow=None):
        """Retrieve a page using its display name.
        Args:
            display_name: Name of the page to retrieve.
        Returns:
            A Dialogflow page instance if found, else None.
        """   
        try:
            request = dialogflowcx.ListPagesRequest(parent=parent_flow)
            response = self.client.list_pages(request=request)
        except Exception as e:
            error_logger.error('error trying to get page by display name with error: ' + str(e))
            raise Exception('Failed to get page by display name.')
        for page in response:
            if page.display_name == display_name:
                return page
        return None

    def create_or_update_page(self, page, parent_flow):
        """Create a new page or update an existing one in a flow.
        Args:
            page: Page instance to be created or updated.
            intent: Intent related to the page. It is a parent string 'parent/...
        Returns:
            Created or updated Dialogflow page instance, or False if an error occurred.
        """      
        try:
            existing_page = self.get_page_by_display_name(page.display_name, parent_flow=parent_flow)
            if not existing_page:
                # create new page
                info_logger.info(f'creating page {page.display_name}')                    
                page = self.client.create_page(page=page, parent=parent_flow)

            else:
                # update new page
                error_logger.info(f"Page {page.display_name} already exists. Updating...")
                page = self.update_page(page=existing_page, new_page=page)
                
            if isinstance(page, tuple):
                page = page[0]
            return page
        except Exception as e:
            error_logger.warning(f'page {page.display_name} could not be created by error:' + str(e))
            return page

    def update_page(self, page, new_page=None, transition_route=None):
        if transition_route != None:
            page.transition_routes.append(transition_route)
        if new_page:
            page.entry_fulfillment = new_page.entry_fulfillment
        try:
            update_mask = field_mask.FieldMask(paths=["transition_routes", 'entry_fulfillment'])
            request = dialogflowcx.UpdatePageRequest(
                    page=page,
                    update_mask=update_mask
                )
            updated_page = self.client.update_page(request=request)
            return updated_page
        except Exception as e:
            error_logger.error(f"Error updating  page {page}: {e} ")
    
    def create_end_flow_page(self, parent_flow, message="Gracias por interactuar con nosotros. ¡Hasta pronto!"):
        """Crea una página 'EndFlow' con un mensaje de despedida personalizado.

        Args:
            parent_flow (str): El flujo padre donde se creará la página.
            message (str, optional): El mensaje de despedida. Por defecto es "Gracias por interactuar con nosotros. ¡Hasta pronto!".

        Returns:
            dialogflowcx.Page: La página 'EndFlow' creada o actualizada.
        """
        # Verificar si la página 'EndFlow' ya existe
        existing_page = self.get_page_by_display_name("EndFlow", parent_flow=parent_flow)
        
        # Crear o actualizar la página 'EndFlow'
        page = dialogflowcx.Page()
        page.display_name = "EndFlow"
        page.entry_fulfillment = dialogflowcx.Fulfillment(messages=[dialogflowcx.ResponseMessage(text=dialogflowcx.ResponseMessage.Text(text=[message]))])
    
        if not existing_page:
            # Si la página no existe, crearla
            return self.client.create_page(page=page, parent=parent_flow)
        else:
            # Si la página ya existe, actualizarla
            page.name = existing_page.name
            return self.update_page(page=existing_page, new_page=page)

class TransitionRouteManager:
    
    def __init__(self, dialogflow_factory, flow_client, parent_flow, pages_manager):
        self.client = dialogflow_factory.transition_route_client()
        self.flow_client = flow_client
        self.pages_manager = pages_manager
        self.parent_flow = parent_flow
    
    def add_transition_route_to_new_flow(self, intent_name, target_flow_name):
        flow = self.flow_client.get_flow(name=self.parent_flow)
        transition_route = dialogflowcx.TransitionRoute(intent=intent_name, target_flow=target_flow_name)
        return self._add_transition_route(flow, transition_route, target_flow_name)

    def set_transition_from_default_start_page(self, intent_name, target_page_name, new_flow):
        transition_route = dialogflowcx.TransitionRoute(intent=intent_name, target_page=target_page_name)
        return self._add_transition_route(new_flow, transition_route, target_page_name)

    def _add_transition_route(self, flow, transition_route, target_name):
        if not any(route.intent == transition_route.intent for route in flow.transition_routes):
            flow.transition_routes.append(transition_route)
            update_mask = field_mask.FieldMask(paths=["transition_routes"])
            request = dialogflowcx.UpdateFlowRequest(flow=flow, update_mask=update_mask)
            try:
                return self.flow_client.update_flow(request=request)
            except Exception as e:
                error_logger.error(f"Error trying to add transition route for {target_name}: {e}")
                raise
        return None








