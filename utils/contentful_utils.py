from loggers.logger import get_logger
import pandas as pd


info_logger = get_logger("info")
error_logger = get_logger("error")
debug_logger = get_logger("debug")


class ContentfulUtils:
    
    @staticmethod
    def build_payload_response(chips, type_of_option):
            """Convert chips from contentful floow['startNode]['chips'] to Dialogflow payload response format.
            Args:
                chips: List of chip items.

            Returns:
                A Dialogflow payload message.
            """
            options = []
            options = [{'text': chip['text'], 'url': chip['url']} if 'url' in chip else {'text': chip['text']} for chip in chips]
            payload_schema = {"RichContent": [
                            [
                                {"options": options,
                                'type': type_of_option
                                }
                            ]
                        ]
                    }
            return payload_schema
       
    @staticmethod
    def build_pandas_dataframes_for_all_content_types_with_related_entry_values(data: list[dict]) -> dict:
            dataframes = {}
            info_logger.info("creating dataframes with all content")
            for key, dataset in data.items():
                    df = pd.DataFrame(dataset)
                    dataframes[key] = df
            return dataframes 

    @staticmethod
    def export_dict_content_types_with_related_entry_dataframe_to_excel(dataframes: dict):
            info_logger.info("Exporting dataframes to excel")
            try:
                with pd.ExcelWriter('output.xlsx') as writer:
                    for data_type, data_list in dataframes.items():
                        data_list.to_excel(writer, sheet_name=data_type, index=False)
                info_logger.info("Exported dataframes to excel successfully")
                return True
            except Exception as e:
                error_logger.error(f'error trying to export dataframes to excel: {e}')

    @staticmethod
    def find_entity_type(entity_value, entity_types_dict):

        for entity in entity_types_dict:
            try:
                for value in entity['entityValue']:
                    if value['entityValue'] == entity_value:
                        return entity['entityType']
            except Exception as e:
                error_logger.error(f"Failed to find_entity_type: {e}")
                raise Exception("Failed to find_entity_type")
        return None