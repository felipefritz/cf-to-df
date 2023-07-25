
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