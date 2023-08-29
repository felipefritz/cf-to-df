import unidecode
from google.cloud.dialogflowcx_v3beta1.types.response_message import ResponseMessage
from google.cloud.dialogflowcx_v3beta1.types.page import Page
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx
from google.protobuf import struct_pb2

from loggers.logger import get_logger


info_logger = get_logger("info")
error_logger = get_logger("error")
debug_logger = get_logger("debug")
warning_logger = get_logger("warning")


class DialogFlowUtils:
    """
    DialogFlowUtils contains utility methods for handling specific tasks related to Dialogflow.

    This class provides static methods to validate and modify flow content, convert chips
    to the Dialogflow payload response format, and other related tasks.

    Attributes:
        None

    Methods:
        add_entry_fulfillment_to_start_page(pages_manager, flow, page): Add entry fulfillment to a father page.
        add_parameter_to_page: "Add a dialog flow parameter to a page.
        add_entity_type_to_page_parameters:
        add_fallback_event_handler_to_page: Add a fallback event handler to a given page. The event will be  sys.no-match
        clean_display_name: Convert special chars to valid chars or -
        flow_validations(pages_manager, entity_type_manager, flow): Validate and modify flow based on its content.

    Note:
        All methods in this class are static and can be called without creating an instance.
    """
   
    @staticmethod
    def add_parameter_to_page(page, parameter_type: str, parameter_name: str, parent, is_required: bool = True, entry_fulfillment=None):
        """Add a dialog flow parameter to a page. It can be extended to include more parameters.
            For now only works for entity types.
        Args:
            page (_type_): _description_
            parameter_name (_type_): _description_
            entity_type_url (_type_): _description_
        """
        # Crear una instancia de parámetro
        parameter = dialogflowcx.Form.Parameter()
        # Asignar el nombre del parámetro
        parameter.display_name = parameter_name
        
        # Si se proporciona entry_fulfillment, lo agregamos al parámetro
        if entry_fulfillment:
            # Crear un FillBehavior
            fill_behavior = dialogflowcx.Form.Parameter.FillBehavior()
            # Asignar el entry_fulfillment como initialPromptFulfillment
            fill_behavior.initial_prompt_fulfillment = dialogflowcx.Fulfillment(messages=entry_fulfillment)
            # Aquí también puedes configurar repromptEventHandlers si es necesario
            # fill_behavior.reprompt_event_handlers = ...
            parameter.fill_behavior = fill_behavior
        # Asignar el EntityType para el parámetro
        if parameter_type == 'entity_type' and parent:
            try:
                parameter.entity_type = parent.name
                parameter.required = is_required
                if not page.form.parameters:
                    page.form.parameters = []
                page.form.parameters.append(parameter)
            except Exception as e:
                error_logger.error(f"error to add parameter to page: {e}")
        return page

        # para agregar los entry fulfillment a los parametros de rutas
    
    @staticmethod
    def add_fulfillment_to_route(father_page, condition, entry_fulfillment, pages_manager):
        try:
            # Verificar si la condición ya existe en las rutas de transición de la página
            existing_route = next((route for route in father_page.transition_routes if route.condition == condition), None)

            if existing_route:
                # Si la ruta ya existe, simplemente agregamos o actualizamos el entry_fulfillment
                existing_route.trigger_fulfillment = dialogflowcx.Fulfillment(
                    messages=[dialogflowcx.ResponseMessage(text=dialogflowcx.ResponseMessage.Text(text=[entry_fulfillment]))]
                )
            else:
                # Si la ruta no existe, la creamos y agregamos el entry_fulfillment
                route = dialogflowcx.TransitionRoute(condition=condition)
                route.trigger_fulfillment = dialogflowcx.Fulfillment(
                    messages=[dialogflowcx.ResponseMessage(text=dialogflowcx.ResponseMessage.Text(text=[entry_fulfillment]))]
                )
                father_page.transition_routes.append(route)

            # Actualizar la página
            return pages_manager.update_page(father_page)

        except Exception as e:
            error_logger.error("Error al agregar fulfillment a la ruta: " + str(e))
 
    @staticmethod
    def add_condition_route_to_page(father_page, condition,  pages_manager, children_page_parent=None, entry_fulfillment=None):
        try:
            # Verificar si alguna condición en las rutas de transición ya utiliza el mismo nombre de parámetro
            if not any(route.condition == condition for route in father_page.transition_routes):
                # Si children_page_parent es None, no asignamos target_page
                if children_page_parent:
                    
                    route = dialogflowcx.TransitionRoute(condition=condition, target_page=children_page_parent)
                else:
                    route = dialogflowcx.TransitionRoute(condition=condition)

                # Si se proporciona un entry_fulfillment, lo agregamos a la ruta de transición
                if entry_fulfillment:
                    route.trigger_fulfillment = dialogflowcx.Fulfillment(
                        messages=[dialogflowcx.ResponseMessage(text=dialogflowcx.ResponseMessage.Text(text=[entry_fulfillment]))]
                    )

                father_page.transition_routes.append(route)
            else:
                warning_logger.warning(f"La condición '{condition}' ya existe en la página {father_page.display_name}.")
        except Exception as e:
            error_logger.error("error adding transition route to page:" + str(e))
        return pages_manager.update_page(father_page)
   
    @staticmethod
    def add_fallback_event_handler_to_page(page: Page, fallback_message: str):
        """Add a fallback event handler to a given page. The event will be  sys.no-match

        Args:
            page: Page instance to which the fallback handler will be added.
            fallback_message: Fallback message text string.

        Returns:
            Updated Dialogflow page instance with the added fallback handler.
        """
        event = "sys.no-match"
        # fallback response
        text_response_content = ResponseMessage.Text(text=[fallback_message])
        text_response = ResponseMessage(text=text_response_content)
        # create a fulfillment and assign the message
        fallback_fulfillment = dialogflowcx.Fulfillment(messages=[text_response])
        # Create Event Handler for  the fallback and add it to the page
        fallback_event_handler = dialogflowcx.EventHandler(event=event, trigger_fulfillment=fallback_fulfillment)
                                                          
        if not page.event_handlers:
            page.event_handlers = []
        page.event_handlers.append(fallback_event_handler)
        return page

    @staticmethod
    def add_entity_type_as_parameter_to_page(page, entity_type_manager, entity_type, entry_fulfillment=None):
        entity_type_name = DialogFlowUtils.clean_display_name(entity_type.replace(" ", "-"))          
        entity_type_parent = entity_type_manager.get_entity_type_by_display_name(entity_type_name)
        parameters = {'page': page,
                        'parameter_type': 'entity_type',
                        'parameter_name': entity_type_name,
                        'is_required': True,
                        'parent': entity_type_parent}
        
        if entry_fulfillment:
            parameters['entry_fulfillment'] = entry_fulfillment
            
        DialogFlowUtils.add_parameter_to_page(**parameters)
        return page
    
    @staticmethod
    def build_entry_fulfillment_from_page(flow: dict):
        """
        Add entry fulfillment to a father page.

        Args:
            pages_manager (PageManager): Instance of the PageManager.
            flow (dict): Flow dictionary containing chips.
            page: Page where the fulfillment will be added.

        Returns:
            page: Page with added entry fulfillment.
        """
        messages = []
        text_message = dialogflowcx.ResponseMessage()
        if 'entry_fulfillment' in flow:
            text_message.text.text.append(flow['entry_fulfillment'])
            messages.append(text_message)

        if 'buttons' in flow:
            custom_payload = flow['buttons']
            # Convertir el dict a un Struct
            payload_struct = struct_pb2.Struct()
            payload_struct.update(custom_payload)
            payload_message_button = dialogflowcx.ResponseMessage(payload=payload_struct)
            messages.append(payload_message_button)

        if len(flow['payload_responses']) > 0:
            custom_payload = flow['payload_responses']
            # Convertir el dict a un Struct
            payload_struct = struct_pb2.Struct()
            payload_struct.update(custom_payload)
            # Crear el mensaje de respuesta con el payload
            payload_message = dialogflowcx.ResponseMessage(payload=payload_struct)
            messages.append(payload_message)
        # page.entry_fulfillment = dialogflowcx.Fulfillment(messages=messages)
        
        return messages 

    @staticmethod
    def clean_display_name(name: str):
        """Convert special chars to valid chars or -

        Returns:
            Información converted to Informacion
        """
        # Convert chars no ASCII to the equivalent ASCII
        cleaned_name = unidecode.unidecode(name)
        # only valid chars or -
        cleaned_name = ''.join(
            ch for ch in cleaned_name if ch.isalnum() or ch == '-')
        return cleaned_name

    @staticmethod
    def page_validations(page, entity_type_manager, page_dict, is_start_page=False):
        """Perform validations and modifications based on flow content.
            It will validate the fallbacks messages, entityTypes adn from contentful flow
        Args:
            pages_manager (PageManager): Instance of the PageManager.
            entity_type_manager (EntityTypeManager): Instance of the EntityTypeManager.
            paged_dict (dict): is a page from contentful flow as a dictionary
        Returns:
            page: The validated and possibly modified page.
        """
        
        if 'fallback_message' in page_dict:
            fallback_message = page_dict['fallback_message']
            DialogFlowUtils.add_fallback_event_handler_to_page(page=page, fallback_message=fallback_message)
        
        entry_fulfillment = DialogFlowUtils.build_entry_fulfillment_from_page(page_dict)                           
        if is_start_page:
            if isinstance(page_dict['start_page_entity_types'], list):
                for index, entity_type in enumerate(page_dict['start_page_entity_types']):
                    if 'entityType' in entity_type:
                        if index == 0: # the first entity type should have the entry fulfillments
                            DialogFlowUtils.add_entity_type_as_parameter_to_page(page=page,
                                                                             entity_type_manager=entity_type_manager,
                                                                             entity_type=entity_type['entityType'],
                                                                             entry_fulfillment=entry_fulfillment)
                        else:                                            
                            DialogFlowUtils.add_entity_type_as_parameter_to_page(page=page,
                                                                             entity_type_manager=entity_type_manager,
                                                                             entity_type=entity_type['entityType'])
        else:
            DialogFlowUtils.add_entity_type_as_parameter_to_page(page=page,
                                                                 entity_type_manager=entity_type_manager,
                                                                 entity_type=page_dict['entityType'],
                                                                 entry_fulfillment=entry_fulfillment)
                                                                 

        
        return page

    @staticmethod
    def set_end_conversation_action(father_page, pages_manager, endflow_page ,condition):
        # Crear una ruta de transición con la acción sys.end-conversation
        transition_route = dialogflowcx.TransitionRoute(target_page=endflow_page.name, condition=condition)
        
        # Actualizar la página padre con la nueva ruta de transición
        pages_manager.update_page(page=father_page, transition_route=transition_route)

     # @staticmethod
