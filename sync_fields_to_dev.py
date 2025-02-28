#!/usr/bin/env python
"""
Sync custom fields, activity types, lead statuses, and opportunity statuses from a Close.io production 
instance to a development instance.

This script connects to the Close.io API and synchronizes:
- Custom fields for leads, contacts, opportunities, and activities
- Custom activity types
- Lead statuses
- Opportunity statuses

Usage:
    python fetch_custom_fields.py

Requirements:
    - Close.io API keys for both production and development environments
    - The closeio Python package
    - python-dotenv (optional, for .env file support)
"""

import os
import json
import sys
import time
from closeio_api import Client

# Try to import dotenv for .env file support
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    print("Note: Install python-dotenv for .env file support: pip install python-dotenv")

def get_api_keys():
    """Get the API keys from environment variables or prompt the user."""
    prod_api_key = os.environ.get('CLOSEIO_API_KEY_PROD')
    dev_api_key = os.environ.get('CLOSEIO_API_KEY_DEV')
    
    if not prod_api_key:
        prod_api_key = input('Please enter your Close.io PRODUCTION API key: ')
    
    if not dev_api_key:
        dev_api_key = input('Please enter your Close.io DEVELOPMENT API key: ')
    
    return prod_api_key, dev_api_key

def fetch_custom_fields(api_key):
    """Fetch all custom fields from Close.io using the correct endpoints."""
    api = Client(api_key)
    
    # Dictionary to store all custom fields by type
    all_custom_fields = {}
    
    # List of endpoints to fetch custom fields from
    endpoints = [
        ('lead', 'Lead Custom Fields'),
        ('contact', 'Contact Custom Fields'),
        ('opportunity', 'Opportunity Custom Fields'),
        ('activity', 'Activity Custom Fields'),
        ('shared', 'Shared Custom Fields')
    ]
    
    # Fetch custom fields from each endpoint
    for endpoint, label in endpoints:
        try:
            endpoint_path = f'custom_field/{endpoint}/'
            print(f"Fetching {label} from {endpoint_path}...")
            custom_fields = api.get(endpoint_path)
            all_custom_fields[endpoint] = custom_fields
        except Exception as e:
            print(f"Error fetching {label}: {e}")
    
    return all_custom_fields

def fetch_custom_activity_types(api_key):
    """Fetch all custom activity types from Close.io."""
    api = Client(api_key)
    
    try:
        print("Fetching Custom Activity Types...")
        activity_types = api.get('custom_activity/')
        return activity_types
    except Exception as e:
        print(f"Error fetching Custom Activity Types: {e}")
        return None

def fetch_lead_statuses(api_key):
    """Fetch all lead statuses from Close.io."""
    api = Client(api_key)
    
    try:
        print("Fetching Lead Statuses...")
        statuses = api.get('status/lead/')
        return statuses
    except Exception as e:
        print(f"Error fetching Lead Statuses: {e}")
        return None

def fetch_opportunity_statuses(api_key):
    """Fetch all opportunity statuses from Close.io."""
    api = Client(api_key)
    
    try:
        print("Fetching Opportunity Statuses...")
        statuses = api.get('status/opportunity/')
        return statuses
    except Exception as e:
        print(f"Error fetching Opportunity Statuses: {e}")
        return None

def create_custom_activity_types(dev_api_key, activity_types):
    """Create custom activity types in the development environment."""
    if not activity_types or not activity_types.get('data'):
        print("No custom activity types to create.")
        return {'created': [], 'failed': [], 'skipped': []}
    
    api = Client(dev_api_key)
    
    # Track results
    created_types = []
    failed_types = []
    skipped_types = []
    
    # Get existing activity types in dev environment
    try:
        existing_types = api.get('custom_activity/')
        existing_type_names = [t.get('name') for t in existing_types.get('data', [])]
    except Exception as e:
        print(f"Error fetching existing activity types: {e}")
        existing_type_names = []
    
    # Create activity type mapping (prod ID -> dev ID)
    activity_type_mapping = {}
    
    # Process each activity type
    for activity_type in activity_types.get('data', []):
        type_name = activity_type.get('name', 'Unknown')
        type_id = activity_type.get('id', 'Unknown')
        
        # Skip if already exists
        if type_name in existing_type_names:
            print(f"Skipping activity type {type_name} (already exists in dev environment)")
            
            # Find the ID of the existing type
            for existing_type in existing_types.get('data', []):
                if existing_type.get('name') == type_name:
                    activity_type_mapping[type_id] = existing_type.get('id')
                    break
                    
            skipped_types.append({
                'name': type_name,
                'id': type_id,
                'dev_id': activity_type_mapping.get(type_id)
            })
            continue
        
        # Prepare activity type data for creation
        type_data = {
            'name': type_name
        }
        
        # Add optional fields if they exist
        if activity_type.get('description'):
            type_data['description'] = activity_type.get('description')
            
        if activity_type.get('api_create_only') is not None:
            type_data['api_create_only'] = activity_type.get('api_create_only')
            
        if activity_type.get('editable_with_roles'):
            type_data['editable_with_roles'] = activity_type.get('editable_with_roles')
        
        # Create the activity type
        try:
            print(f"Creating custom activity type: {type_name}")
            new_type = api.post('custom_activity/', data=type_data)
            
            # Store mapping of production ID to development ID
            activity_type_mapping[type_id] = new_type.get('id')
            
            created_types.append({
                'name': type_name,
                'id': new_type.get('id'),
                'prod_id': type_id
            })
            
            print(f"Successfully created {type_name} with ID: {new_type.get('id')}")
            
            # Sleep briefly to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Failed to create {type_name}: {e}")
            failed_types.append({
                'name': type_name,
                'error': str(e)
            })
    
    return {
        'created': created_types,
        'failed': failed_types,
        'skipped': skipped_types,
        'mapping': activity_type_mapping
    }

def create_custom_fields(dev_api_key, all_custom_fields, activity_type_mapping=None):
    """Create custom fields in the development environment."""
    api = Client(dev_api_key)
    
    # Track results
    created_fields = []
    failed_fields = []
    skipped_fields = []
    
    # Process each type of custom field
    for field_type, fields in all_custom_fields.items():
        if not fields.get('data'):
            continue
            
        print(f"\nCreating {field_type.upper()} custom fields in development environment...")
        
        for field in fields['data']:
            field_name = field.get('name', 'Unknown')
            field_id = field.get('id', 'Unknown')
            
            # Check if field already exists in dev environment
            try:
                existing_fields = api.get(f'custom_field/{field_type}/')
                exists = any(f.get('name') == field_name for f in existing_fields.get('data', []))
                
                if exists:
                    print(f"Skipping {field_name} (already exists in dev environment)")
                    skipped_fields.append({
                        'type': field_type,
                        'name': field_name,
                        'id': field_id
                    })
                    continue
            except Exception as e:
                print(f"Error checking if field exists: {e}")
            
            # Prepare field data for creation
            field_data = {
                'name': field_name,
                'type': field.get('type')
            }
            
            # Add optional fields if they exist
            if field.get('description'):
                field_data['description'] = field.get('description')
                
            if field.get('choices'):
                field_data['choices'] = field.get('choices')
                
            if field.get('accepts_multiple_values'):
                field_data['accepts_multiple_values'] = field.get('accepts_multiple_values')
                
            if field.get('required'):
                field_data['required'] = field.get('required')
                
            if field.get('editable_with_roles'):
                field_data['editable_with_roles'] = field.get('editable_with_roles')
                
            if field.get('referenced_custom_type_id'):
                field_data['referenced_custom_type_id'] = field.get('referenced_custom_type_id')
                
            if field.get('back_reference_is_visible') is not None:
                field_data['back_reference_is_visible'] = field.get('back_reference_is_visible')
            
            # Special handling for activity custom fields
            if field_type == 'activity':
                # Get the original custom_activity_type_id from production
                prod_activity_type_id = field.get('custom_activity_type_id')
                
                if not prod_activity_type_id:
                    print(f"Skipping {field_name} (no custom_activity_type_id found)")
                    skipped_fields.append({
                        'type': field_type,
                        'name': field_name,
                        'id': field_id,
                        'reason': 'No custom_activity_type_id found'
                    })
                    continue
                
                # Map to development custom_activity_type_id
                if activity_type_mapping and prod_activity_type_id in activity_type_mapping:
                    field_data['custom_activity_type_id'] = activity_type_mapping[prod_activity_type_id]
                else:
                    print(f"Skipping {field_name} (could not map custom_activity_type_id)")
                    skipped_fields.append({
                        'type': field_type,
                        'name': field_name,
                        'id': field_id,
                        'reason': 'Could not map custom_activity_type_id'
                    })
                    continue
            
            # Create the field
            try:
                print(f"Creating {field_type} custom field: {field_name}")
                endpoint_path = f'custom_field/{field_type}/'
                new_field = api.post(endpoint_path, data=field_data)
                
                created_fields.append({
                    'type': field_type,
                    'name': field_name,
                    'id': new_field.get('id'),
                    'prod_id': field_id
                })
                
                print(f"Successfully created {field_name} with ID: {new_field.get('id')}")
                
                # Sleep briefly to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Failed to create {field_name}: {e}")
                failed_fields.append({
                    'type': field_type,
                    'name': field_name,
                    'error': str(e)
                })
    
    return {
        'created': created_fields,
        'failed': failed_fields,
        'skipped': skipped_fields
    }

def sync_lead_statuses(dev_api_key, prod_statuses):
    """Sync lead statuses between environments."""
    if not prod_statuses or not prod_statuses.get('data'):
        print("No lead statuses to sync.")
        return {'created': [], 'removed': [], 'failed': []}
    
    api = Client(dev_api_key)
    
    # Track results
    created_statuses = []
    removed_statuses = []
    failed_statuses = []
    
    # Get existing statuses in dev environment
    try:
        existing_statuses = api.get('status/lead/')
        dev_statuses = {s.get('label'): s for s in existing_statuses.get('data', [])}
        prod_status_labels = {s.get('label') for s in prod_statuses.get('data', [])}
    except Exception as e:
        print(f"Error fetching existing lead statuses: {e}")
        return {'created': [], 'removed': [], 'failed': []}
    
    # Create missing statuses
    for status in prod_statuses.get('data', []):
        label = status.get('label')
        if label not in dev_statuses:
            try:
                print(f"Creating lead status: {label}")
                new_status = api.post('status/lead/', data={'label': label})
                created_statuses.append({
                    'label': label,
                    'id': new_status.get('id')
                })
                print(f"Successfully created lead status: {label}")
                time.sleep(0.5)  # Avoid rate limiting
            except Exception as e:
                print(f"Failed to create lead status {label}: {e}")
                failed_statuses.append({
                    'label': label,
                    'error': str(e)
                })
    
    # Remove statuses that don't exist in production
    for label, status in dev_statuses.items():
        if label not in prod_status_labels:
            try:
                print(f"Removing lead status: {label}")
                api.delete(f"status/lead/{status.get('id')}/")
                removed_statuses.append({
                    'label': label,
                    'id': status.get('id')
                })
                print(f"Successfully removed lead status: {label}")
                time.sleep(0.5)  # Avoid rate limiting
            except Exception as e:
                print(f"Failed to remove lead status {label}: {e}")
                failed_statuses.append({
                    'label': label,
                    'error': str(e)
                })
    
    return {
        'created': created_statuses,
        'removed': removed_statuses,
        'failed': failed_statuses
    }

def sync_opportunity_statuses(dev_api_key, prod_statuses):
    """Sync opportunity statuses between environments."""
    if not prod_statuses or not prod_statuses.get('data'):
        print("No opportunity statuses to sync.")
        return {'created': [], 'removed': [], 'failed': []}
    
    api = Client(dev_api_key)
    
    # Track results
    created_statuses = []
    removed_statuses = []
    failed_statuses = []
    
    # Get existing statuses in dev environment
    try:
        existing_statuses = api.get('status/opportunity/')
        dev_statuses = {s.get('label'): s for s in existing_statuses.get('data', [])}
        prod_status_labels = {s.get('label') for s in prod_statuses.get('data', [])}
    except Exception as e:
        print(f"Error fetching existing opportunity statuses: {e}")
        return {'created': [], 'removed': [], 'failed': []}
    
    # Create missing statuses
    for status in prod_statuses.get('data', []):
        label = status.get('label')
        if label not in dev_statuses:
            try:
                print(f"Creating opportunity status: {label}")
                new_status = api.post('status/opportunity/', data={
                    'label': label,
                    'type': status.get('type', 'active')  # Include the status type
                })
                created_statuses.append({
                    'label': label,
                    'id': new_status.get('id'),
                    'type': status.get('type')
                })
                print(f"Successfully created opportunity status: {label}")
                time.sleep(0.5)  # Avoid rate limiting
            except Exception as e:
                print(f"Failed to create opportunity status {label}: {e}")
                failed_statuses.append({
                    'label': label,
                    'error': str(e)
                })
    
    # Remove statuses that don't exist in production
    for label, status in dev_statuses.items():
        if label not in prod_status_labels:
            try:
                print(f"Removing opportunity status: {label}")
                api.delete(f"status/opportunity/{status.get('id')}/")
                removed_statuses.append({
                    'label': label,
                    'id': status.get('id')
                })
                print(f"Successfully removed opportunity status: {label}")
                time.sleep(0.5)  # Avoid rate limiting
            except Exception as e:
                print(f"Failed to remove opportunity status {label}: {e}")
                failed_statuses.append({
                    'label': label,
                    'error': str(e)
                })
    
    return {
        'created': created_statuses,
        'removed': removed_statuses,
        'failed': failed_statuses
    }

def display_custom_fields(all_custom_fields):
    """Display custom fields in a structured format."""
    if not all_custom_fields:
        print("No custom fields found.")
        return
    
    # Display custom fields by type
    for field_type, fields in all_custom_fields.items():
        if field_type == 'schemas':
            continue  # We'll display schemas separately
            
        print(f"\n{'=' * 30}")
        print(f"{field_type.upper()} CUSTOM FIELDS")
        print(f"{'=' * 30}")
        
        if not fields.get('data'):
            print(f"No {field_type} custom fields found.")
            continue
        
        print(f"Found {len(fields['data'])} {field_type} custom fields:")
        print("-" * 80)
        
        for field in fields['data']:
            print(f"Field ID: {field.get('id')}")
            print(f"Name: {field.get('name')}")
            print(f"Type: {field.get('type')}")
            
            # Display additional properties based on field type
            if field.get('choices'):
                print("Choices:")
                for choice in field.get('choices', []):
                    print(f"  - {choice}")
            
            if field.get('accepts_multiple_values'):
                print("Accepts multiple values: Yes")
            
            if field.get('required'):
                print("Required: Yes")
                
            if field.get('description'):
                print(f"Description: {field.get('description')}")
                
            if field.get('custom_activity_type_id'):
                print(f"Custom Activity Type ID: {field.get('custom_activity_type_id')}")
            
            print("-" * 80)

def display_custom_activity_types(activity_types):
    """Display custom activity types in a structured format."""
    if not activity_types or not activity_types.get('data'):
        print("No custom activity types found.")
        return
    
    print(f"\n{'=' * 30}")
    print("CUSTOM ACTIVITY TYPES")
    print(f"{'=' * 30}")
    
    print(f"Found {len(activity_types['data'])} custom activity types:")
    print("-" * 80)
    
    for activity_type in activity_types['data']:
        print(f"Type ID: {activity_type.get('id')}")
        print(f"Name: {activity_type.get('name')}")
        
        if activity_type.get('description'):
            print(f"Description: {activity_type.get('description')}")
            
        if activity_type.get('api_create_only'):
            print("API Create Only: Yes")
            
        print("-" * 80)

def display_statuses(statuses, title):
    """Display statuses in a structured format."""
    if not statuses or not statuses.get('data'):
        print(f"No {title} found.")
        return
    
    print(f"\n{'=' * 30}")
    print(title)
    print(f"{'=' * 30}")
    
    print(f"Found {len(statuses['data'])} statuses:")
    print("-" * 80)
    
    for status in statuses['data']:
        print(f"ID: {status.get('id')}")
        print(f"Label: {status.get('label')}")
        
        if 'type' in status:  # For opportunity statuses
            print(f"Type: {status.get('type')}")
            
        print("-" * 80)

def display_results(results, title):
    """Display the results of the creation process."""
    print("\n\n" + "=" * 50)
    print(title)
    print("=" * 50)
    
    if 'created' in results:
        print(f"\nCreated: {len(results['created'])} items")
        for item in results['created']:
            # Handle both name and label fields
            name = item.get('name') or item.get('label')
            type_info = f" ({item['type']})" if 'type' in item else ''
            print(f"  - {name}{type_info}: {item['id']}")
    
    if 'skipped' in results:
        print(f"\nSkipped: {len(results['skipped'])} items (already exist)")
        for item in results['skipped']:
            # Handle both name and label fields
            name = item.get('name') or item.get('label')
            type_info = f" ({item['type']})" if 'type' in item else ''
            print(f"  - {name}{type_info}")
    
    if 'failed' in results:
        print(f"\nFailed: {len(results['failed'])} items")
        for item in results['failed']:
            # Handle both name and label fields
            name = item.get('name') or item.get('label')
            type_info = f" ({item['type']})" if 'type' in item else ''
            print(f"  - {name}{type_info}: {item['error']}")
    
    if 'removed' in results:
        print(f"\nRemoved: {len(results['removed'])} items")
        for item in results['removed']:
            # Handle both name and label fields
            name = item.get('name') or item.get('label')
            type_info = f" ({item['type']})" if 'type' in item else ''
            print(f"  - {name}{type_info}: {item['id']}")

def main():
    """Main function to run the script."""
    # Get API keys
    prod_api_key, dev_api_key = get_api_keys()
    
    # Fetch data from production
    print("\nFetching data from PRODUCTION environment...")
    prod_custom_fields = fetch_custom_fields(prod_api_key)
    prod_activity_types = fetch_custom_activity_types(prod_api_key)
    prod_lead_statuses = fetch_lead_statuses(prod_api_key)
    prod_opportunity_statuses = fetch_opportunity_statuses(prod_api_key)
    
    # Save the raw responses to JSON files for reference
    with open('data/custom_fields_prod.json', 'w') as f:
        json.dump(prod_custom_fields, f, indent=2)
    print("\nRaw custom fields response from production saved to data/custom_fields_prod.json")
    
    if prod_activity_types:
        with open('data/custom_activity_types_prod.json', 'w') as f:
            json.dump(prod_activity_types, f, indent=2)
        print("Raw activity types response from production saved to data/custom_activity_types_prod.json")
    
    if prod_lead_statuses:
        with open('data/lead_statuses_prod.json', 'w') as f:
            json.dump(prod_lead_statuses, f, indent=2)
        print("Raw lead statuses response from production saved to data/lead_statuses_prod.json")
    
    if prod_opportunity_statuses:
        with open('data/opportunity_statuses_prod.json', 'w') as f:
            json.dump(prod_opportunity_statuses, f, indent=2)
        print("Raw opportunity statuses response from production saved to data/opportunity_statuses_prod.json")
    
    # Display production data
    print("\nPRODUCTION ENVIRONMENT CUSTOM FIELDS:")
    display_custom_fields(prod_custom_fields)
    
    if prod_activity_types:
        print("\nPRODUCTION ENVIRONMENT CUSTOM ACTIVITY TYPES:")
        display_custom_activity_types(prod_activity_types)
    
    if prod_lead_statuses:
        print("\nPRODUCTION ENVIRONMENT LEAD STATUSES:")
        display_statuses(prod_lead_statuses, "LEAD STATUSES")
    
    if prod_opportunity_statuses:
        print("\nPRODUCTION ENVIRONMENT OPPORTUNITY STATUSES:")
        display_statuses(prod_opportunity_statuses, "OPPORTUNITY STATUSES")
    
    # Confirm before proceeding
    confirm = input("\nDo you want to sync these items to the DEVELOPMENT environment? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # First create custom activity types
    activity_type_mapping = None
    if prod_activity_types and prod_activity_types.get('data'):
        print("\nCreating custom activity types in development environment...")
        activity_type_results = create_custom_activity_types(dev_api_key, prod_activity_types)
        
        # Save results to a JSON file
        with open('data/custom_activity_types_creation_results.json', 'w') as f:
            json.dump(activity_type_results, f, indent=2)
        print("\nActivity type creation results saved to data/custom_activity_types_creation_results.json")
        
        # Display results
        display_results(activity_type_results, "CUSTOM ACTIVITY TYPE CREATION RESULTS")
        
        # Get the mapping for use with activity custom fields
        activity_type_mapping = activity_type_results.get('mapping', {})
    
    # Then create custom fields
    print("\nCreating custom fields in development environment...")
    field_results = create_custom_fields(dev_api_key, prod_custom_fields, activity_type_mapping)
    
    # Save results to a JSON file
    with open('data/custom_fields_creation_results.json', 'w') as f:
        json.dump(field_results, f, indent=2)
    print("\nCustom field creation results saved to data/custom_fields_creation_results.json")
    
    # Display results
    display_results(field_results, "CUSTOM FIELD CREATION RESULTS")
    
    # Sync lead statuses
    if prod_lead_statuses and prod_lead_statuses.get('data'):
        print("\nSyncing lead statuses...")
        lead_status_results = sync_lead_statuses(dev_api_key, prod_lead_statuses)
        
        # Save results to a JSON file
        with open('data/lead_statuses_sync_results.json', 'w') as f:
            json.dump(lead_status_results, f, indent=2)
        print("\nLead status sync results saved to data/lead_statuses_sync_results.json")
        
        # Display results
        display_results(lead_status_results, "LEAD STATUS SYNC RESULTS")
    
    # Sync opportunity statuses
    if prod_opportunity_statuses and prod_opportunity_statuses.get('data'):
        print("\nSyncing opportunity statuses...")
        opportunity_status_results = sync_opportunity_statuses(dev_api_key, prod_opportunity_statuses)
        
        # Save results to a JSON file
        with open('data/opportunity_statuses_sync_results.json', 'w') as f:
            json.dump(opportunity_status_results, f, indent=2)
        print("\nOpportunity status sync results saved to data/opportunity_statuses_sync_results.json")
        
        # Display results
        display_results(opportunity_status_results, "OPPORTUNITY STATUS SYNC RESULTS")

if __name__ == "__main__":
    main()
