from loggers.logger import get_logger
from clients.dialogflow_client import AbstractDialogFlowClient, AgentManager, EntityTypeManager, PageManager, IntentManager, FlowManager, TransitionRouteManager


logger = get_logger()


class DialogflowServiceCX:

    def __init__(self, client: AbstractDialogFlowClient, agent_name: str):
        logger.info("initializing DialogflowService")
        self.agent_manager = AgentManager(client, agent_name)
        self.flow_manager = FlowManager(client, self.agent_manager)
        self.intent_manager = IntentManager(client, self.agent_manager.agent_id)
        self.entity_type_manager = EntityTypeManager(client, self.agent_manager.agent_id)
        self.transition_route_manager = TransitionRouteManager(client,
                                                               self.flow_manager.client,
                                                               self.flow_manager.parent)
        self.pages_manager = PageManager(client, 
                                         self.agent_manager.agent_id,
                                         self.flow_manager.default_flow_id,
                                         self.transition_route_manager)

    def create_entity_types(self, entity_types):
        
        entity_types = [self.entity_type_manager.create_or_update_entity_type(display_name=entity_type.get('entityType'),
                                                                    entities_with_synonyms=entity_type['entityValue'])
                        for entity_type in entity_types]
        return entity_types
    
    def create_intents(self, flows: list):
        intents =  self.intent_manager.get_intents_all()
        
        for flow in flows:
            self._add_parent_to_intent(flow, intents)
            display_name = flow['intent']
            default_training_phrase = flow['question'].strip()
            self.intent_manager.create_intent_if_not_exists(display_name=display_name,
                                                  training_phrase=default_training_phrase)

    def create_pages(self, intents_list):
        responses = []
        for intent in intents_list:
            response = self.pages_manager.create_page(intent)
        return

    def create_pages_faq(self, intents_list):
        pages_created = []
        for intent in intents_list:
            response = self.pages_manager.create_or_update_page_faq(intent, intent['startNode']['text'])
            pages_created.append(response)
        return pages_created
    
    def delete_pages(self):
        return self.pages_manager.delete_all_pages()
    
    def _add_parent_to_intent(self, flow, intents):
        for intent in intents:
            if flow['intent'] == intent['display_name']:
                flow['parent'] = intent['parent']
                return flow
    


























class DialogflowService:
    
    def __init__(self, client: AbstractDialogFlowClient):
            self.client = client
    
    def get_intent_by_display_name(self, display_name):
        # Get the list of all intents.
        parent = f"projects/{self.client.project_id}/agent"
        intents_client = self.client.get_intents_client()
        intents = intents_client.list_intents(request={"parent": parent})

        # Search for the intent with the given display name.
        for intent in intents:
            if intent.display_name == display_name:
                return intent
        return None
        
    def create_entity_type(self, display_name, kind, entities):
        entity_type_client = self.client.get_entity_types_client()
        entity_type = dialogflow_v2.EntityType(
            display_name=display_name,
            kind=kind,
            entities=entities
        )
        response = entity_type_client.create_entity_type(
            request={"parent": self.parent, "entity_type": entity_type}
        )
        print(f"Entity type created: {response}")
        return response

    def create_entities(self, entity_type_id, entities):
        entities_client = self.client.get_entity_types_client()
        parent = f'{self.parent}/entityTypes/{entity_type_id}'

        for entity in entities:
            entity_obj = dialogflow_v2.EntityType.Entity(value=entity['value'], synonyms=entity['synonyms'])
            response = entities_client.create_entity(request={"parent": parent, "entity": entity_obj})
            print(f"Entity created: {response}")
            
    def create_intent(self, intent, end_interaction=False):
        parent = f"projects/{self.client.project_id}/agent"
        intent.end_interaction = end_interaction
        intents_client = self.client.get_intents_client()
        response = intents_client.create_intent(request={"parent": parent, "intent": intent})
        print(f"Intent created: {response}")
        return response
    
    def create_intent_with_chips(dialogflow_service, intent_name, response_text, chips):
        # Crear la parte de texto del mensaje
        text_part = dialogflow_v2.Intent.Message.Text(text=[response_text])

        # Crear botones para la tarjeta utilizando los chips
        buttons = []
        for chip in chips:
            button = dialogflow_v2.Intent.Message.Card.Button(text=chip['text'])
            buttons.append(button)

        # Crear una tarjeta con los botones
        card_part = dialogflow_v2.Intent.Message.Card(title="Seleccione una opción:", buttons=buttons)

        # Crear la intención con el texto y la tarjeta
        intent = dialogflow_v2.Intent(
            display_name=intent_name,
            messages=[text_part, card_part]
        )

        response = dialogflow_service.create_intent(intent)
        return response
    
    def create_intent_with_buttons(self, display_name, message_texts, buttons):
        parent = f"projects/{self.client.project_id}/agent"
        
        # Creando la estructura de la tarjeta con botones
        card = dialogflow_v2.Intent.Message.Card(
            title="Por favor, elige una opción",
            buttons=[dialogflow_v2.Intent.Message.Card.Button(text=button['text'], postback=button['postback']) for button in buttons]
        )
        message = dialogflow_v2.Intent.Message(card=card)

        # Creando el intent
        intent = dialogflow_v2.Intent(display_name=display_name, messages=[message])
        response = self.client.get_intents_client().create_intent(request={"parent": parent, "intent": intent})
        print("Intent with buttons created: {}".format(response))
        return response

    def create_fallback_intent(self, fallback_response_text):
        parent = f"projects/{self.client.project_id}/agent"
        text_part = dialogflow_v2.Intent.Message.Text(text=[fallback_response_text])
        fallback_intent = dialogflow_v2.Intent(
            display_name="Fallback",
            messages=[text_part],
            is_fallback=True
        )
        intents_client = self.client.get_intents_client()
        response = intents_client.create_intent(request={"parent": parent, "intent": fallback_intent})
        print(f"Fallback Intent created: {response}")
        return response
    