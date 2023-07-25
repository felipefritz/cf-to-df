from contentful import Client
import os
from clients.logger import get_logger
import pandas as pd
import numpy as np 


logger = get_logger()
space_id = os.getenv('CONTENTFUL_SPACE_ID')
api_key = os.getenv('CONTENTFUL_delivery_API_KEY')


class ContentfulService:

    def __init__(self, space_id, access_token, environment='master'):
            self.client = Client(space_id, access_token, environment=environment)
            self.content_types = self.client.content_types()
            self.content_types_names = self.get_content_type_names()
            self.all_entries = self.client.entries({'limit': 1000})
            self.all_entries_dict = {entry.id: entry for entry in self.all_entries}

            self.entries_by_content_type = self.__get_entries_by_content_type()
            self.flows = self.client.entries({'limit': 1000, 'content_type': 'flow'})
        
    def get_entry_by_id(self, id):
        """ Get an entry by its id. Return None if not found. """
        return self.all_entries_dict.get(id)
        
    def get_content_type_names(self) -> list[str]:
        return [content_type.id for content_type in self.content_types.items]
    
    def expand_list_of_dicts(self, df, column):
        # Descomponemos la lista en múltiples filas
        df = df.explode(column)

        # Si la columna todavía contiene diccionarios, los expande en columnas separadas
        if df[column].apply(lambda x: isinstance(x, dict)).any():
            dict_df = df[column].apply(pd.Series)
            dict_df.columns = [f"{column}_{col}" for col in dict_df.columns]
            df = df.drop(columns=[column]).join(dict_df)

        return df
        
    def expand_dict_or_list(self, row):
        if isinstance(row, list):
            if all(isinstance(i, dict) for i in row):
                # Convierte cada diccionario en un DataFrame y agrega todos los DataFrames a una lista
                df_list = [pd.DataFrame([d]) for d in row]

                # Comprueba si todos los datos en los DataFrames son numéricos
                if all(df.applymap(np.isreal).all().all() for df in df_list):
                    # Si df_list no está vacía, concatena sus elementos
                    if df_list:
                        return pd.concat(df_list, axis=0)
                    else:
                        return pd.DataFrame()
                else:
                    # Combina los DataFrames en un solo DataFrame
                    df = pd.concat(df_list, axis=0)
                    # Elimina las columnas con 'object object'
                    df = df.loc[:, df.applymap(lambda x: x != 'object object').all()]
                    return df
            else:
                return pd.DataFrame(row)
        elif isinstance(row, dict):
            return pd.DataFrame([row])
        else:
            return pd.DataFrame()

        
    def extract_values_from_all_entries(self, data: list[dict]):
        if len(data) == 0 and not hasattr(data, 'items'):
            return []

        data_by_type = {}
        dataframes = {}
        
        for item in data.items:
            item_dict = {
                **item.raw['fields'],
                'locale': item.raw['sys']['locale'],
                'id': item.id,
                'type': item.content_type.id,
                'fields_keys': [key for key, val in item.raw['fields'].items() if isinstance(val, dict) or isinstance(val, list)],
            }

            if item.content_type.id in data_by_type:
                data_by_type[item.content_type.id].append(item_dict)
            else:
                data_by_type[item.content_type.id] = [item_dict]

        for items in data_by_type.values():
            for item in items:
                self.extract_sys_ids(item)
                        
        for key, dataset in data_by_type.items():
            df = pd.DataFrame(dataset)
            dataframes[key] = df
            
        with pd.ExcelWriter('output.xlsx') as writer:
            for data_type, data_list in dataframes.items():
                data_list.to_excel(writer, sheet_name=data_type, index=False)
            
        return dataframes

    
  
    def extract_sys_ids(self, element):
        for key, value in element.items():
            if isinstance(value, dict):
                if 'sys' in value and 'id' in value['sys']:
                    entry_id = value['sys']['id']
                    entry = self.get_entry_by_id(entry_id)  # Get the entry by id
                    if entry is not None:
                        element[key] = {**entry.raw['fields']}  # Replace the value with the entry fields
                        self.extract_sys_ids(element[key])  # Recursive call for the new fields
            elif isinstance(value, list):
                for i, subvalue in enumerate(value):
                    if isinstance(subvalue, dict) and 'sys' in subvalue and 'id' in subvalue['sys']:
                        entry_id = subvalue['sys']['id']
                        entry = self.get_entry_by_id(entry_id)  # Get the entry by id
                        if entry is not None:
                            value[i] = {**entry.raw['fields']}  # Replace the value with the entry fields
                            self.extract_sys_ids(value[i]) 

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
                entries = [
                    entry for entry in self.all_entries if entry.content_type.id == content_type.id]
                
                entries_by_content_type.append(
                    {'display_field': content_type.display_field,
                     'content_type_name': content_type.id,
                     'entries': entries})

                logger.info(f"Fetching entries for {content_type.id}")
            except Exception as e:
                logger.error(f'error: {e}')
                continue

        return entries_by_content_type

    def get_entity_types_with_values(self):
        results = []
        entry_name = 'entityType'
        entity_types_items = next(
            (entry['entries'] for entry in self.entries_by_content_type if entry_name in entry['content_type_name']), None)

        entities = next(
            (entry['entries'] for entry in self.entries_by_content_type if 'entity' in entry['content_type_name']), None)

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

    def separate_data_by_type(self, df: pd.DataFrame) -> dict:
        dataframes = {group: data for group, data in df.groupby('type')}
        return dataframes
        

cf_service = ContentfulService(space_id, api_key)
data = cf_service.extract_values_from_all_entries(cf_service.all_entries)

flow_df = data['flow']

pass


            
        # data_type, data_list in data_by_type.items():
        #    df = pd.DataFrame(data_list)
            # df.to_excel('results.xlsx', sheet_name=data_type, index=False)
        #    df_dict_results[data_type] = df

        # return df_dict_results