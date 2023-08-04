from abc import ABC, abstractmethod
from typing import List

from google.cloud import  dialogflowcx_v3beta1 as dialogflowcx
from google.oauth2 import service_account
from loggers.logger import get_logger

logger = get_logger()


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
    
    def get_transition_route_group_client(self):
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

    def create_entity_type(self, display_name, entities_with_synonyms):
        entities = []
        display_name = display_name.replace(' ', '-')
        
        for entity in entities_with_synonyms:
            value = entity['entityValue']
            synonyms = entity.get('synonyms', [value])  # Utiliza el valor principal como sinónimo si no hay otros sinónimos
            entities.append(dialogflowcx.EntityType.Entity(value=value, synonyms=synonyms))

        entity_type = dialogflowcx.EntityType(
            display_name=display_name,
            entities=entities,
            kind=dialogflowcx.EntityType.Kind.KIND_MAP,
            enable_fuzzy_extraction=True,
        )
        try:
            response = self.client.create_entity_type(parent=self.parent, entity_type=entity_type)
            print(f"Entity type created: {response}")
            return response
        except Exception as e:
            if "already exists" in str(e):
                logger.warning(f"Entity type with display name '{display_name}' already exists. Continuing...")
            else:
                logger.error(f"An unexpected error occurred while creating entity type {display_name}: {e}")
                return False

    
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


class TransitionRouteGroupManager:
    def __init__(self, dialogflow_factory, agent_id, flow_id):
        self.dialogflow_factory = dialogflow_factory
        self.client = dialogflow_factory.get_transition_route_group_client()
        self.parent = dialogflow_factory.get_transition_group_parent(agent_id, flow_id)
        self.transition_route_group_id = None
        self.transition_route_group = self.get_or_create_default_transition_route_group()
        
    def get_or_create_default_transition_route_group(self):
        
        request = dialogflowcx.ListTransitionRouteGroupsRequest(parent=self.parent)
        transition_route_groups_pager = self.client.list_transition_route_groups(request=request)
        transition_route_groups_list = list(transition_route_groups_pager)

        if len(transition_route_groups_list) > 0:
            self.transition_route_group_id = transition_route_groups_list[0].name.split('/')[-1]
            return transition_route_groups_list[0]

        transition_route_group_to_create = dialogflowcx.TransitionRouteGroup(display_name="DefaultTransitionRouteGroup")
        transition_route_group = self.client.create_transition_route_group(parent=self.parent, transition_route_group=transition_route_group_to_create)
        self.transition_route_group_id = transition_route_group.name.split('/')[-1]
        return transition_route_group

    def get_transition_route_group(self, transition_route_group_id):
        name = f'{self.parent}/transitionRouteGroups/{transition_route_group_id}'
        return self.client.get_transition_route_group(name=name)

    def create_transition_route_group(self, transition_route_group):
        request = dialogflowcx.CreateTransitionRouteGroupRequest(
            parent=self.parent,
            transition_route_group=transition_route_group)

        return self.client.create_transition_route_group(request=request)

    def update_transition_route_group(self, transition_route_group_id, transition_route_group):
        name = f'{self.parent}/transitionRouteGroups/{transition_route_group_id}'
        request = dialogflowcx.UpdateTransitionRouteGroupRequest(
            transition_route_group=transition_route_group,
            update_mask={"paths": ["display_name", "transition_routes"]})
        request.transition_route_group.name = name

        return self.client.update_transition_route_group(request=request)



class PageManager:
    def __init__(self, dialogflow_factory, agent_id, flow_id):
        self.client = dialogflow_factory.get_pages_client()
        self.parent_flow = f"{dialogflow_factory.get_agent_parent(agent_id)}/flows/{flow_id}"

    def create_pages(self, intents_list, form, transition_routes, flow_manager):
        for intent in intents_list:
            # Crea una página
            page = dialogflowcx.Page(
                display_name=intent['display_name'],
                # ... otros detalles de la página ...
            )
            page = self.client.create_page(parent=flow_manager.parent, page=page)
        return 


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
            print(f"Intent created: {display_name}")
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
















    
"""class DialogFlowClientEssentials(AbstractDialogFlowClient):

    def __init__(self, project_id, key_file):
        self.agents_client = None
        self.credentials = service_account.Credentials.from_service_account_file(key_file)
        self.project_id = project_id
        
    def get_agents_client(self):
        return dialogflow_v2.AgentsClient(credentials=self.credentials)

    def get_contexts_client(self):
        return dialogflow_v2.ContextsClient(credentials=self.credentials)

    def get_entity_types_client(self):
        return dialogflow_v2.EntityTypesClient(credentials=self.credentials)

    def get_fulfillments_client(self):
        return dialogflow_v2.FulfillmentsClient(credentials=self.credentials)  

    def get_intents_client(self):
        return dialogflow_v2.IntentsClient(credentials=self.credentials)

    """