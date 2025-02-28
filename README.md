## Close API

[![PyPI version](https://badge.fury.io/py/closeio.svg)](https://badge.fury.io/py/closeio) [![CircleCI](https://circleci.com/gh/closeio/closeio-api.svg?style=shield&circle-token=e12bb3b9bcf749c2e7a5691e8101c3e585b19742)](https://circleci.com/gh/closeio/closeio-api)

A convenient Python wrapper for the [Close](https://close.com/) API.

- API docs: [http://developer.close.com](http://developer.close.com)
- Support: [support@close.com](mailto:support@close.com?Subject=API%20Python%20Client)

### Installation

`pip install closeio`

### Sample Usage (of API client)

```python
from closeio_api import Client

api = Client('YOUR_API_KEY')

# post a lead
lead = api.post('lead', data={'name': 'New Lead'})

# get 5 most recently updated opportunities
opportunities = api.get('opportunity', params={'_order_by': '-date_updated', '_limit': 5})

# fetch multiple leads (using search syntax)
lead_results = api.get('lead', params={
    '_limit': 10,
    '_fields': 'id,display_name,status_label',
    'query': 'custom.my_custom_field:"some_value" status:"Potential" sort:updated'
})
```

### Utility Scripts

#### Environment Synchronization

The repository includes a utility script `fetch_custom_fields.py` that helps synchronize various configurations between Close.io environments (e.g., production to development). This script can sync:

- Custom fields (Lead, Contact, Opportunity, Activity)
- Custom activity types
- Lead statuses
- Opportunity statuses

Usage:
```bash
# Set up environment variables in .env file
CLOSEIO_API_KEY_PROD=your_production_api_key
CLOSEIO_API_KEY_DEV=your_development_api_key

# Run the script
python sync_fields_to_dev.py
```

The script will:
1. Fetch all configurations from the production environment
2. Save the raw data to JSON files in the `data/` directory
3. Create missing items in the development environment
4. Remove items from development that don't exist in production
5. Generate detailed reports of all changes

### Example scripts

Check out [https://github.com/closeio/closeio-api-scripts](https://github.com/closeio/closeio-api-scripts) for helpful scripts already written to accomplish some common tasks.

### Other Languages

There are unofficial API clients available in other languages too, thanks to some awesome contributors:

 - Ruby: [simple example](https://gist.github.com/philfreo/9359930) that uses [RestClient](https://github.com/rest-client/rest-client), or use [taylorbrook's gem](https://github.com/taylorbrooks/closeio)
 - PHP: [simple example](https://gist.github.com/philfreo/5406540) or https://github.com/loopline-systems/closeio-api-wrapper or https://github.com/TheDeveloper/closeio-php-sdk or [one for use in Laravel](https://github.com/gyurobenjamin/closeio-laravel-api)
 - Node.js: https://github.com/closeio/closeio-node
 - C#: https://github.com/MoreThanRewards/CloseIoDotNet
 - Elixir: https://github.com/nested-tech/closex or https://github.com/taylorbrooks/ex_closeio
 - Go: https://github.com/veyo-care/closeio-golang-client or https://github.com/AnalyticalFlavorSystems/closeio-go
