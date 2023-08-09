from loggers.logger import get_logger
import pandas as pd


logger = get_logger()

def get_all_contentful_entries(contentful_client):
        all_entries = []
        limit = 1000
        skip = 0
        total = None

        while total is None or len(all_entries) < total:
            response = contentful_client.entries({'limit': limit, 'skip': skip})
            if total is None:
                total = response.total
            all_entries.extend(response.items)
            skip += limit

        return all_entries


def get_entity_types_with_values(contenful_service):
        results = []
        entry_name = 'entityType'
        entity_types_items = next(
            (entry['entries'] for entry in contenful_service.entries_by_content_type if entry_name in entry['content_type_name']), None)

        entities = next(
            (entry['entries'] for entry in contenful_service.entries_by_content_type if 'entity' in entry['content_type_name']), None)

        for entity_type in entity_types_items:
            for value in entity_type.raw['fields']['entityValue']:
                result_dict = {
                    'entity_type_id': entity_type.raw['sys']['id'],
                    'content_type': entry_name,
                    'entity_type_name': entity_type.raw['fields']['entityType'],
                    'entity_type_value_id': value['sys']['id'],
                }

                # find matching entity and add entityValue
                for entity in entities:
                    if entity.raw['sys']['id'] == result_dict['entity_type_value_id']:
                        result_dict['entity_value'] = entity.raw['fields']['entityValue']

                results.append(result_dict)

        return results
    
    
def build_pandas_dataframes_for_all_content_types_with_related_entry_values(data: list[dict]) -> dict:
        dataframes = {}
        logger.info("creating dataframes with all content")
        for key, dataset in data.items():
                df = pd.DataFrame(dataset)
                dataframes[key] = df
        return dataframes 


def export_dict_content_types_with_related_entry_dataframe_to_excel(dataframes: dict):
        logger.info("Exporting dataframes to excel")
        try:
            with pd.ExcelWriter('output.xlsx') as writer:
                for data_type, data_list in dataframes.items():
                    data_list.to_excel(writer, sheet_name=data_type, index=False)
            logger.info("Exported dataframes to excel successfully")
            return True
        except Exception as e:
            logger.error(f'error trying to export dataframes to excel: {e}')
