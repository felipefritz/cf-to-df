from collections import defaultdict
from google.cloud import dialogflowcx_v3beta1 as dialogflowcx

from loggers.logger import get_logger
from clients.dialogflow_client import DialogFlowCXClientFactory, AgentManager, EntityTypeManager, \
    PageManager, IntentManager, FlowManager, TransitionRouteManager
from utils.utils_dialogflow import DialogFlowUtils


info_logger = get_logger("info")
error_logger = get_logger("error")
debug_logger = get_logger("debug")


class DialogflowServiceCX:

    def __init__(self, client: DialogFlowCXClientFactory, agent_name: str):
        info_logger.info("initializing DialogflowService")
        self.agent_manager = AgentManager(client, agent_name)
        self.flow_manager = FlowManager(client, self.agent_manager)
        self.intent_manager = IntentManager(
            client, self.agent_manager.agent_id)
        self.entity_type_manager = EntityTypeManager(
            client, self.agent_manager.agent_id)
        self.pages_manager = PageManager(client,
                                         self.agent_manager.agent_id,
                                         self.flow_manager.default_flow_id,
                                         )
        self.transition_route_manager = TransitionRouteManager(client,
                                                               self.flow_manager.client,
                                                               self.flow_manager.parent,
                                                               self.pages_manager
                                                               )
    
    def _add_parent_to_intent(self, flow):
        """Adds parent details as string to the intent within a flow.

        Args:
            flow (dict): Flow configuration.

        Returns:
            dict: Updated flow dict with a new key and value 
                key: parent
                value: parent url required by dialog flow such as parent/project_id/____/agent/____/....
        """
        intents = self.intent_manager.get_intents_all()
        for intent in intents:
            if flow['intent'] == intent['display_name']:
                flow['parent_intent'] = intent['parent']
                return flow

    def _get_direct_subpages(self, parent_page_name, all_subpages):
        return [subpage for subpage in all_subpages if subpage['parent'] == parent_page_name]
    
    def group_by_page_group(self, flows_list):
        grouped_pages = defaultdict(list)
        for page in flows_list:
            grouped_pages[page['page_group']].append(page)
        return grouped_pages
    
    def create_entity_types(self, entity_types):

        entity_types = [self.entity_type_manager.create_or_update_entity_type(display_name=entity_type.get('entityType'),
                                                                              entity_types=entity_type['entityValue'])
                        for entity_type in entity_types]
        return entity_types

    def create_intents(self, intents: list):
        for intent in intents:
            self._add_parent_to_intent(intent)
            display_name = intent['intent']
            default_training_phrase = intent['default_training_phrase'].strip()
            self.intent_manager.create_intent_if_not_exists(display_name=display_name,
                                                            training_phrase=default_training_phrase)

    def create_page(self, page_dict: dict, dialogflow_flow_parent_name: str, is_start_page=False):
        if is_start_page:
            self._add_parent_to_intent(page_dict)
        page = dialogflowcx.Page()
        page.display_name = page_dict['display_name']
        page = DialogFlowUtils.page_validations(page=page, page_dict=page_dict, is_start_page=is_start_page, entity_type_manager=self.entity_type_manager)
        page = self.pages_manager.create_or_update_page(page=page, parent_flow=dialogflow_flow_parent_name)
        return page
    
    def create_flows(self, flows_list):
        for flow in flows_list:
            new_flow_object = self.flow_manager.create_flow(flow['display_name']) 
            sub_pages = sorted(flow['subpages'], key=lambda x: x['depth'])
            
            if new_flow_object.name != '':  # If new flow is created, then create pages and sub pages in the new flow
                sub_pages[0]['start_page_entity_types'] = flow['start_page_entity_types']
                sub_pages[0]['intent'] = flow['intent']
                group = self.group_by_page_group(flow['subpages'])
                            
                
                self.create_flows_from_grouped_pages(new_flow_object=new_flow_object, grouped_pages=group)

    def create_flows_from_grouped_pages(self, grouped_pages, new_flow_object):
        for page_group, pages in grouped_pages.items():

            for sub_page in pages:
                if sub_page['parent'] == None:
                    sub_page['entityValues']
                    sub_page['parent'] = sub_page['display_name']
                    start_page = self.create_page(page_dict=pages[0], dialogflow_flow_parent_name=new_flow_object.name, is_start_page=True)
                    self.transition_route_manager.add_transition_route_to_new_flow(intent_name=sub_page['parent_intent'], target_flow_name=new_flow_object.name)
                    self.transition_route_manager.set_transition_from_default_start_page(intent_name=sub_page['parent_intent'],
                                                                                     new_flow=new_flow_object, target_page_name=start_page.name) 
                father_page_name = sub_page['parent']
                sub_page_object = self.create_page(page_dict=sub_page, dialogflow_flow_parent_name=new_flow_object.name)         
                father_page = self.pages_manager.get_page_by_display_name(display_name=father_page_name, parent_flow=new_flow_object.name)
                #if sub_page['depth'] == 1:
                #    sub_page['entityValues'] = sub_pages[0]['entityValues'] + sub_page['entityValues']
                
                for entity_type_value in sub_page['entityValues']:
                        condition = f'{sub_page["route_params_entity_types"]} = "{entity_type_value}"'
                        
                        # check if subpage is endflow, 
                        if sub_page['is_end_flow']:
                            # if sub_page is end flow, add entry fulfillment message to the father page route with condition
                            DialogFlowUtils.add_fulfillment_to_route(father_page=father_page,
                                                                    condition=condition,
                                                                    entry_fulfillment=sub_page['entry_fulfillment'],
                                                                    pages_manager=self.pages_manager)

                        else:
                            # create a new page with transition route from father page
                            DialogFlowUtils.add_condition_route_to_page(father_page=father_page,
                                                                        children_page_parent=sub_page_object.name,
                                                                        condition=condition,
                                                                        pages_manager=self.pages_manager)
    
    def create_subpages_in_flow(self, new_flow_object, sub_pages: list[dict]):
        for sub_page in sub_pages:
            if sub_page['parent'] != None:
                father_page_name = sub_page['parent']
                sub_page_object = self.create_page(page_dict=sub_page, dialogflow_flow_parent_name=new_flow_object.name)         
                father_page = self.pages_manager.get_page_by_display_name(display_name=father_page_name, parent_flow=new_flow_object.name)
                if sub_page['depth'] == 1:
                    sub_page['entityValues'] = sub_pages[0]['entityValues'] + sub_page['entityValues']
                
                for entity_type_value in sub_page['entityValues']:
                        condition = f'{sub_page["route_params_entity_types"]} = "{entity_type_value}"'
                        
                        # check if subpage is endflow, 
                        if sub_page['is_end_flow']:
                            # if sub_page is end flow, add entry fulfillment message to the father page route with condition
                            DialogFlowUtils.add_fulfillment_to_route(father_page=father_page,
                                                                    condition=condition,
                                                                    entry_fulfillment=sub_page['entry_fulfillment'],
                                                                    pages_manager=self.pages_manager)

                        else:
                            # create a new page with transition route from father page
                            DialogFlowUtils.add_condition_route_to_page(father_page=father_page,
                                                                        children_page_parent=sub_page_object.name,
                                                                        condition=condition,
                                                                        pages_manager=self.pages_manager)

   