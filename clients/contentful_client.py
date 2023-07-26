from contentful import Client, errors
from abc import ABC, abstractmethod
from loggers.logger import get_logger


logger = get_logger()

class AbstractContentfulClient(ABC):

    @abstractmethod
    def content_types(self):
        pass

    @abstractmethod
    def entries(self, limit):
        pass


class ContentfulClient(AbstractContentfulClient):
    
    def __init__(self, space_id, access_token, environment='master'):
        self.client = Client(space_id, access_token, environment=environment)

    def content_types(self):
        return self.client.content_types()

    def entries(self, limit=1000):
        entries = self.client.entries({'limit': limit})
        return entries

