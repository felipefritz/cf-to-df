from loggers.logger import get_logger
from clients.contentful_client import ContentfulClient
from utils.utils_dialogflow import DialogFlowUtils
from utils.contentful_utils import ContentfulUtils

info_logger = get_logger("info")
error_logger = get_logger("error")
debug_logger = get_logger("debug")


class ContentfulServiceError(Exception):
    """Custom exception for ContentfulService class."""
    pass


class ContentfulService:

    def __init__(self, client: ContentfulClient):
        info_logger.info(f"Initializing ContentfulService...")
        self.client = client
        self._content_types = None
        self._all_entries = None
        self._all_entries_dict = None
        self._data_ready_to_use = None
        self._entity_types = None
        self._flows = None

    @property
    def all_entries(self):
        if self._all_entries is None:
            self._all_entries = self._fetch_all_entries()
        return self._all_entries

    @property
    def content_types(self):
        if self._content_types is None:
            self._content_types = self.client.content_types()
        return self._content_types

    @property
    def data_ready_to_use(self):
        if self._data_ready_to_use is None:
            self._data_ready_to_use = self.extract_values_from_all_entries(self.all_entries)
        return self._data_ready_to_use
    
    @property
    def entity_types(self):
        if self._entity_types is None:
            data = self.data_ready_to_use
            if data and 'entityType' in data:
                self._entity_types = data['entityType'].to_dict('records')
            else:
                self._entity_types = []
        return self._entity_types
    
    @property
    def flows(self):
        if self._flows is None:
            data = self.data_ready_to_use
            if data and 'flow' in data:
                self._flows = data['flow'].to_dict('records') 
            else:
                self._flows = []       
        return self._flows
   
    @property
    def flows_with_subpages(self):
        flows_with_subpages = []
        if not self.flows:
            return flows_with_subpages
        
        flows_no_faq = [flow for flow in self.flows if 'intent' in flow and not flow['intent'].startswith('faq')]
        for i, flow in enumerate(flows_no_faq):
            try:
                sub_pages = self._map_subpages_from_flow(flow['startNode'], 
                                                         chip_text=flow['key'],
                                                         entity_types_dict=flow['flowEntityTypes'])
                # start flow data with subpages
                flows_with_subpages.append({'display_name': flow['key'], 
                                            'intent': flow['intent'],
                                            'locale': flow['locale'],
                                            'question': flow['question'],
                                            'payload_responses': [],
                                            'entry_fulfillment': flow['startNode']['text'],
                                            'start_page_entity_types': flow['flowEntityTypes'],
                                            'fallback_message': flow['startNode']['fallbacks'][0]['text'],
                                            'subpages': sub_pages})
                
                for subpage in sub_pages:
                    if subpage['parent'] is None:  
                        flows_with_subpages[i]['payload_responses'] = ContentfulUtils.build_payload_response(flow['startNode']['chips'],
                                                                                                             type_of_option='chips')
                        
            except KeyError as e:
                error_logger.error(f"Key error in flows_with_subpages: {e}")
                raise ContentfulServiceError(f"Failed to process flow due to missing key: {e}")
            except Exception as e:
                error_logger.error(f"Unexpected error in flows_with_subpages: {e}")
                raise ContentfulServiceError("Failed to process flow due to an unexpected error")
        
        return flows_with_subpages
  
    @property
    def intents(self):
        intents = []
        if self.flows:
            for flow in self.flows:
                intents.append({'intent': flow['intent'], 'default_training_phrase': flow['question']})
        return intents
    
    def extract_values_from_all_entries(self, data: list[dict], export_to_excel=False) -> dict:
        """This function extracts all values from all entries by content type and return them as a dict of dataframe.
        Also it is possible to export all entries by content type in excel format.

        Args:
            data (list[dict]): Are all entries from contentful api. Each entry is a contentful.Entry object.
            export_to_excel (bool, optional): Export all entries by content type, each conten type by sheets. Defaults to False.

        Returns:
            dict: dict with dataframes for each content type.
        """
        try:
            if len(data) == 0 and not hasattr(data, 'items'):
                error_logger.error("No entries found")
                return {}

            data_by_content_type = self._build_data_by_content_type(data)
            dataframes = ContentfulUtils.build_pandas_dataframes_for_all_content_types_with_related_entry_values(
                data_by_content_type)

        except Exception as e:
            error_logger.error(f"Failed to extract_values_from_all_entries: {e}")
            raise Exception("Failed to extract_values_from_all_entries")
                 
        return dataframes
    
    def get_entry_by_id(self, id) -> dict:
        """ Get an entry by its id. Return None if not found. """
        try:
            entry = self._all_entries_dict.get(id)
            return entry
        except Exception as e:
            error_logger.error(f'error trying to fetch all entries: {e}')
            raise ContentfulServiceError(f'Failed to get entry by id: {e}')  
    
    def _map_subpages_from_flow(self, data, result=None, chip_text=None, parent_name=None,
                                depth=0, entity_types_dict=[], current_entity_value=None,
                                current_entity_type=None,  page_group=None, parent_entity_type=None,
                                parent_entity_values=None):
        # Initialize the results list if is the first time that the function is called
        if result is None:
            result = []

        current_page_name = chip_text if chip_text else data['text']
        combined_page_name = f"{parent_name} > {current_page_name}" if parent_name else current_page_name

        # Si no se ha definido un page_group, se usa el combined_page_name como el page_group
        if not page_group:
            group = combined_page_name.split(">")
            if len(group) >=2:
                page_group = group[1].strip()

        # create the schema for sub pages o child pages in flow
        page_info = {
                "display_name": combined_page_name,
                "entry_fulfillment": data['text'],
                "parent": parent_name,
                "payload_responses": [],
                "depth": depth,
                'is_end_flow': False,
                'entityType': '',
                'entityValues': [],
                'parent_entity_type':parent_entity_type,
                'parent_entity_values': parent_entity_values,
                'route_params_entity_types': '',
                'page_group': page_group  # Agregamos el campo page_group
            }

        try:
            # Handling entityTypes
            
            if 'entityType' in data:
                if 'entityType' in data['entityType']:  # Check if the key exists
                    current_entity_type = DialogFlowUtils.clean_display_name(data['entityType']['entityType'])
                    page_info["entityType"] = current_entity_type
                    page_info["entityValues"] = [ev['entityValue'] for ev in data['entityType']['entityValue']]
            elif current_entity_value:
                found_entity_type = ContentfulUtils.find_entity_type(current_entity_value['entityValue'], entity_types_dict)
                if found_entity_type:
                    page_info["entityType"] = found_entity_type['entityType']
                    page_info["entityValues"] = [current_entity_value['entityValue']]
                    
            if 'entityValues' in data and page_info["entityValues"] == []:
                page_info["entityValues"] =data['entityValues']
            if current_entity_type:
                page_info['route_params_entity_types'] = f"$session.params.{current_entity_type}"

            # check if actual element has chips
            if 'chips' in data:
                for chip in data['chips']:
                    if 'buttons' in chip:
                        page_info['buttons'] = ContentfulUtils.build_payload_response(chip['location']['buttons'], 'button')
                    if not page_info["payload_responses"] and not self.page_already_added(result, page_info):
                        if page_info not in  result:
                            result.append(page_info)
                    # if chip has location, so has a subpage (location), then is added to the dict and call the function recursively
                    if 'location' in chip:
                        
                        if 'buttons' in chip['location']:
                            page_info['buttons'] = ContentfulUtils.build_payload_response(chip['location']['buttons'], 'button')
                            
                        self._map_subpages_from_flow(chip['location'],
                                                     result, chip['text'],
                                                     combined_page_name,
                                                     depth+1,
                                                    parent_entity_type= page_info['entityType'],
                                                     parent_entity_values= page_info['entityValues'],
                                                     current_entity_value=chip.get('entityValue'),
                                                     current_entity_type=current_entity_type)
                    # if chip has not "location" but  has "url" key, then is added to the payload dict"
                    elif 'url' in chip:
                        payload = {
                            "text": chip.get('text', ""),
                            "url": chip.get('url', "")
                        }
                        page_info["payload_responses"].append(payload)

                # IFf the page has "payload" responses, then, add payload responses to page info
                if page_info["payload_responses"]:
                    page_info["payload_responses"] = ContentfulUtils.build_payload_response(page_info["payload_responses"], 'chips')
                    if page_info not in  result:
                        result.append(page_info)

            #if the element has not "url" and "chips",but has "text", then it should be a endflow"
            elif 'text' in data and 'url' not in data and 'chips' not in data:
                page_info["is_end_flow"] = True
                if current_entity_type and not page_info["entityType"]:  # added only if  page_info["entityType"] is empty
                    page_info["entityType"] = current_entity_type
                if current_entity_value and not page_info["entityValues"]:  # added only if page_info["entityValues"] is empty
                    page_info["entityValues"].append(current_entity_value['entityValue'])
                if page_info not in  result:
                            result.append(page_info)
                if not self.page_already_added(result, page_info):
                    if page_info not in  result:
                            result.append(page_info)
        except Exception as e:
            
            error_logger.error(str(e))
        return result
    
    def page_already_added(self, result, page_info):
        return any(page["display_name"] == page_info["display_name"] for page in result)

    def _fetch_all_entries(self):
        try:
            info_logger.info("Fetching all entries")
            all_entries = self.client.entries()
            self._all_entries_dict = {entry.id: entry for entry in all_entries}
            info_logger.info(f"Fetched {len(all_entries)} entries successfully")
            return all_entries
        except Exception as e:
            error_logger.error(f'error trying to fetch all entries: {e}')
            raise ContentfulServiceError(f'Failed to fetch entries from contentful {e}')  
    
    def _extract_sys_ids(self, element):
        for key, value in element.items():
            if isinstance(value, dict):
                if 'sys' in value and 'id' in value['sys']:
                    entry_id = value['sys']['id']
                    entry = self.get_entry_by_id(
                        entry_id)  # Get the entry by id
                    if entry is not None:
                        # Replace the value with the entry fields
                        element[key] = {**entry.raw['fields']}
                        # Recursive call for the new fields
                        self._extract_sys_ids(element[key])
                        
            elif isinstance(value, list):
                for i, subvalue in enumerate(value):
                    if isinstance(subvalue, dict) and 'sys' in subvalue and 'id' in subvalue['sys']:
                        entry_id = subvalue['sys']['id']
                        entry = self.get_entry_by_id(
                            entry_id)  # Get the entry by id
                        if entry is not None:
                            # Replace the value with the entry fields
                            value[i] = {**entry.raw['fields']}
                            self._extract_sys_ids(value[i])

    def _build_data_by_content_type(self, data: list[dict]) -> dict:
        data_by_content_type = {}
        
        info_logger.info(f"Extracting values from entries for content type")
        try:
            for item in data:
                item_dict = {
                    **item.raw['fields'],
                    'locale': item.raw['sys']['locale'],
                    'id': item.id,
                    'type': item.content_type.id,
                    'fields_keys': [key for key, val in item.raw['fields'].items() if isinstance(val, dict) or isinstance(val, list)],
                }

                if item.content_type.id in data_by_content_type:
                    # id is the contenttype name like  flow, entityType,
                    data_by_content_type[item.content_type.id].append(item_dict)
                else:
                    data_by_content_type[item.content_type.id] = [item_dict]
        except Exception as e:
            error_logger.error(f'error trying to _build_data_by_content_type: {e}')
            raise ContentfulServiceError(f'Failed to get entry by id: {e}')  
         
        self._build_data_by_content_type_with_related_entry_values(data_by_content_type)
        return data_by_content_type

    def _build_data_by_content_type_with_related_entry_values(self, data: list[dict]):
        info_logger.info(f"Extracting values from all entries")
        for content_type_name, items in data.items():
            for item in items:
                self._extract_sys_ids(item)
