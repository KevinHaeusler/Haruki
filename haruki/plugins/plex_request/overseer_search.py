import overseerr
from ...constants import OVERSEER_TOKEN, OVERSEER_URL

configuration = overseerr.Configuration(
    host=f"{OVERSEER_URL}/api/v1",

)

# Configure API key authorization: apiKey
configuration.api_key['apiKey'] = OVERSEER_TOKEN


async def get_search_results(media_type, media):
    with overseerr.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = overseerr.SearchApi(api_client)
        query = media  # str |
        page = 1  # float |  (optional) (default to 1)
        language = 'en'  # str |  (optional)

        try:
            # Search for movies, TV shows, or people
            api_response = api_instance.get_search(query, page=page, language=language)
            results = api_response.results if api_response.results else []

            # Access the 'results' attribute which is a list of results
            search_results = []
            for result in results:
                actual_instance = result.actual_instance
                if actual_instance.media_type == media_type:
                    if media_type == 'tv':
                        search_results.append({
                            "id": actual_instance.id,
                            "title": actual_instance.name,
                            "year": actual_instance.first_air_date[:4] if actual_instance.first_air_date else None
                        })
                    else:
                        search_results.append({
                            "id": actual_instance.id,
                            "title": actual_instance.title,
                            "year": actual_instance.release_date[:4] if actual_instance.release_date else None
                        })

            return search_results
        except Exception as e:
            print("Exception when calling SearchApi->get_search: %s\n" % e)
            return 'Search Failed'
