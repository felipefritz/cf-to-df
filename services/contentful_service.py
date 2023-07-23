from contentful import Client
import os
from clients.logger import get_logger


logger = get_logger()
space_id = os.getenv('CONTENTFUL_SPACE_ID')
api_key = os.getenv('CONTENTFUL_delivery_API_KEY')


class ContentfulService:

    def __init__(self, space_id, access_token, environment='master'):
        self.client = Client(space_id, access_token, environment=environment)
        self.entries_by_content_type = []

    def __get_entries_by_content_type(self):
        for content_type in self.content_types.items:
            try:
                entries = self.client.entries(
                    {'content_type': content_type.id})
                self.entries_by_content_type.append({content_type.id: entries})
                logger.info(f"Fetching entries for {content_type.id}")

            except Exception as e:
                logger.error(f'error: {e}')
                continue

    def __get_fields_data_from_entries_by_entry_type_name(self, entry_name):
        self.entity_types = []
        self.__get_entries_by_content_type()

        entity_types_items = next(
            (entry[entry_name].items for entry in self.entries_by_content_type if entry_name in entry), None)

        raw_data = [
            row.raw for row in entity_types_items if hasattr(row, 'raw')]
        fields_data = [row['fields'] for row in raw_data if 'fields' in row]
        return fields_data

    def get_entries(self):
        self.entries = self.client.entries()

    def get_content_types(self):
        self.content_types = self.client.content_types()

    def get_entity_types(self):
        fields_data = self.__get_fields_data_from_entries_by_entry_type_name(
            'entityType')

        for field in fields_data:
            for value in field['entityValue']:
                self.entity_types.append({'entityType':  field['entityType'],
                                          'entityValue_type':  value['sys']['type'],
                                          'entityValue_linktype':  value['sys']['linkType'],
                                          'entityValue_id':  value['sys']['id']
                                          })


cf_service = ContentfulService(space_id, api_key)
cf_service.get_content_types()
cf_service.get_entity_types()
