from loggers.logger import get_logger
from clients.contentful_client import AbstractContentfulClient
from utils.contentful_utils import build_pandas_dataframes_for_all_content_types_with_related_entry_values, \
                                        export_dict_content_types_with_related_entry_dataframe_to_excel

logger = get_logger()


class ContentfulService:

    def __init__(self, client: AbstractContentfulClient):
        logger.info(f"Initializing ContentfulService...")
        self.client = client
        self._content_types = None
        self._all_entries = None
        self._all_entries_dict = None
        self._flows = None
        self._entity_types = None
        self._intents = None
        self._pages = None
        self._data_ready_to_use = None
        
    @property
    def content_types(self):
        if self._content_types is None:
            self._content_types = self.client.content_types()
        return self._content_types

    @property
    def all_entries(self):
        if self._all_entries is None:
            self._all_entries = self._fetch_all_entries()
        return self._all_entries

    @property
    def data_ready_to_use(self):
        if self._data_ready_to_use is None:
            self._data_ready_to_use = self.extract_values_from_all_entries(self.all_entries)
        return self._data_ready_to_use
    
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
    def entity_types(self):
        if self._entity_types is None:
            data = self.data_ready_to_use
            if data and 'entityType' in data:
                self._flows = data['entityType'].to_dict('records')
            else:
                self._flows = []
        return self._flows
    
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
                logger.error("No entries found")
                return {}

            data_by_content_type = self._build_data_by_content_type(data)
            dataframes = build_pandas_dataframes_for_all_content_types_with_related_entry_values(
                data_by_content_type)

            if export_to_excel:
                export_dict_content_types_with_related_entry_dataframe_to_excel(
                    dataframes)
            logger.info(f"Extracted values from all entries successfully")
            
        except Exception as e:
                return 
                logger.error(f"Failed to get data from contentful: {e}")
        return dataframes

    def get_entry_by_id(self, id) -> dict:
        """ Get an entry by its id. Return None if not found. """
        return self._all_entries_dict.get(id)
    
    def _fetch_all_entries(self):
        try:
            logger.info("Fetching all entries")
            all_entries = self.client.entries()
            self._all_entries_dict = {entry.id: entry for entry in all_entries}
            logger.info(f"Fetched {len(all_entries)} entries successfully")
            return all_entries
        except Exception as e:
            logger.error(f'error trying to fetch all entries: {e}')
            return []    
    
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
        
        logger.info(f"Extracting values from entries for content type")
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
                
        self._build_data_by_content_type_with_related_entry_values(data_by_content_type)
        return data_by_content_type

    def _build_data_by_content_type_with_related_entry_values(self, data: list[dict]):
        logger.info(f"Extracting values from all entries")
        for content_type_name, items in data.items():
            logger.info(
                f"Extracting values from content type: {content_type_name}")
            for item in items:
                self._extract_sys_ids(item)
