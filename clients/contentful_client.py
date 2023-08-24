import logging
import sys
from abc import ABC, abstractmethod
from contentful import Client

logging.basicConfig(level=logging.ERROR)


class ContentfulClient:
    
    def __init__(self, space_id, access_token, environment='master'):
        self._client = None
        self.space_id = space_id
        self.access_token = access_token
        self.environment = environment
        
    @property
    def client(self):
        if self._client == None:
            try:
                self._client = Client(space_id=self.space_id,
                                      access_token=self.access_token,
                                      environment=self.environment,
                                      max_include_resolution_depth=20)
            except Exception as e:
                logging.error("Cannot connect to contentful client: %s", str(e))
                sys.exit(1)
            return self._client
    
    def content_types(self):
        return self.client.content_types()

    def entries(self, limit=1000):
        return self.client.entries({'limit': limit})
    
    

