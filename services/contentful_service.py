from contentful import Client
import os
from clients.logger import get_logger


logger = get_logger()
space_id = os.getenv('CONTENTFUL_SPACE_ID')
api_key = os.getenv('CONTENTFUL_delivery_API_KEY')


class ContentfulService:

    def __init__(self, space_id, access_token, environment='master'):
        self.client = Client(space_id, access_token, environment=environment)
        self.content_types = self.client.content_types()
        self.entries = self.client.entries()
        self.entries_by_content_type = self.__get_entries_by_content_type()
        
    def __get_entries_by_content_type(self) -> list[dict]:
        """ Contentful has content types with their associated entries. 
            for instance of this, we need to fetch all entries for each content type.
        row of results:
        
        content_type_name: entity,
        display_field: entityValue,
        entries: [Entry[entity], Entry[entity]] -> Entity is a contenful object type.
        
        return: list[dict]
        """
        
        entries_by_content_type = []
        
        for content_type in self.content_types.items:
            
            try:
                entries = [entry for entry in self.entries if entry.content_type.id == content_type.id]
                entries_by_content_type.append(
                    {'display_field': content_type.display_field,
                     'content_type_name': content_type.id,
                     'entries': entries})

                logger.info(f"Fetching entries for {content_type.id}")
            except Exception as e:
                logger.error(f'error: {e}')
                continue
            
        return entries_by_content_type

    def get_entity_types_with_values(self, entry_name='entityType'):
        results = []
        entity_types_items = next(
            (entry[entry_name].items for entry in self.entries_by_content_type if entry_name in entry), None)

        entities = {
            entity.raw['sys']['id']: entity for entry in self.entries_by_content_type if 'entity' in entry for entity in entry['entity'].items}

        for entity_type in entity_types_items:
            for value in entity_type.raw['fields']['entityValue']:
                result_dict = {
                    'entity_type_id': entity_type.raw['sys']['id'],
                    'entity_type_value_id': value['sys']['id'],
                    'content_type': entry_name,
                    'entity_type_name': entity_type.raw['fields']['entityType'],
                }

                # find matching entity and add entityValue
                matching_entity = entities.get(
                    result_dict['entity_type_value_id'])
                if matching_entity is not None:
                    result_dict['entity_value'] = matching_entity.raw['fields']['entityValue']

                results.append(result_dict)

        return results


cf_service = ContentfulService(space_id, api_key)
cf_service.get_entity_types_with_values()


example = {'flow': {'content_type': 'flow',
                    'intent': 'flow.activacion.info',
                    'question': 'Necesito activar un producto',
                    'id': 'U9MvUcf1GNP0KUQ6MTSkS'},
           'flowEntityTypes': {}
           }
