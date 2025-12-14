# typical setup : C:\Users\phong\Pictures\tools.png
import sys

all_tools = [
    {
        'type': 'function',
        'function': {
            'name': 'get_product_data',  # scrape data

            'description': '''Get data of a product. Use only when user ask about a product. 
            Your input should be of the product only. Example:\n
            user: I want to know the specs of the MSI Katana 15 B13VKF\n\n
            Good input: MSI Katana 15 B13VKF\n
            Bad input: MSI Katana 15 B13VKF specs''',

            'parameters': {
                'type': 'object',
                'properties': {
                    'search_query': {
                        'type': 'string',
                        'description': 'What product to search for.'
                    }
                },
                'required': ['search_query']
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for additional information for unsure user query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_query": {
                        "type": "string",
                        "description": "What to search for on the internet."
                    }
                },
                "required": ["search_query"]
            }
        }
    },
    # {
    #     'type': 'function',
    #     'function': {
    #         'name': 'get_data_online',  # scrape data
    #         'description': '''Get data of a product. Use only when user ask about a product. 
    #         Your input should be of the product only. Example:\n
    #         user: I want to know the specs of the MSI Katana 15 B13VKF\n\n
    #         Good input: MSI Katana 15 B13VKF\n
    #         Bad input: MSI Katana 15 B13VKF specs''',
    #         'parameters': {
    #             'type': 'object',
    #             'properties': {
    #                 'query': {
    #                     'type': 'string',
    #                     'description': 'What product to search for.'
    #                 }
    #             },
    #             'required': ['query']
    #         }
    #     }
    # }
]