from contentful import Client, errors
from logger import get_logger


logger = get_logger()


class ContentfulClient:
    
    def __init__(self, space_id, Content_delivery_api_key):
        self.client = self.authenticate(space_id, Content_delivery_api_key)
        self.is_authenticated = False
        
    def authenticate(self, space_id, access_token, environment='master'):
        
        try:
            client = Client(space_id, access_token, environment=environment)
            self.is_authenticated = True
            logger.info(f"authentication success to contentful client")
            return client
        
        except errors.UnauthorizedError as e:
            logger.error(f"Error occurred during authentication: {e}")
            return False


