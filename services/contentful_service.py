from loggers.logger import get_logger
from clients.contentful_client import AbstractContentfulClient
from services.contentful_utils import build_pandas_dataframes_for_all_content_types_with_related_entry_values, \
                                        export_dict_content_types_with_related_entry_dataframe_to_excel

logger = get_logger()


class ContentfulService:

    def __init__(self, client: AbstractContentfulClient):
        logger.info(f"Initializing ContentfulService...")
        self.client = client
        self.content_types = None
        self.all_entries = None

    def get_content_type_names(self) -> list[str]:
        if not self.content_types:
            self._get_content_types()

        logger.info(f"Fetching content type names")
        content_type_names = [
            content_type.id for content_type in self.content_types.items]
        logger.info("Fetched the following content type names successfully:\n{}".format(
            '\n'.join(content_type_names)))
        return content_type_names

    def get_all_entries(self) -> dict:
        try:
            logger.info("Fetching all entries")
            self.all_entries = self.client.entries()
            self.all_entries_dict = {
                entry.id: entry for entry in self.all_entries}
            logger.info(
                f"Fetched {len(self.all_entries)} entries successfully")
            return self.all_entries

        except Exception as e:
            logger.error(f'error trying to fetch all entries: {e}')

    def get_entry_by_id(self, id) -> dict:
        """ Get an entry by its id. Return None if not found. """
        logger.info(f"Fetching entry with id: {id}")
        return self.all_entries_dict.get(id)

    def extract_values_from_all_entries(self, data: list[dict], export_to_excel=False) -> dict:
        """This function extracts all values from all entries by content type and return them as a dict of dataframe.
        Also it is possible to export all entries by content type in excel format.

        Args:
            data (list[dict]): Are all entries from contentful api. Each entry is a contentful.Entry object.
            export_to_excel (bool, optional): Export all entries by content type, each conten type by sheets. Defaults to False.

        Returns:
            dict: dict with dataframes for each content type.
        """
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
        return dataframes

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

    def _get_content_types(self) -> list[dict]:
        self.content_types = self.client.content_types()

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
                logger.info(
                    f"Extracting related values from entry with id: {item['id']} and conten type {content_type_name}")
                self._extract_sys_ids(item)
