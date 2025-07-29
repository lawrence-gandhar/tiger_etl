# User Group CRUD Operations Documentation

## Overview
This document provides comprehensive documentation for the CRUD (Create, Read, Update, Delete) operations for user groups in the Tiger ETL system.

## Table of Contents
- [Function Reference](#function-reference)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Performance Considerations](#performance-considerations)

## Function Reference

### Create Operations

#### `create_user_group(group_data: Dict[str, Any]) -> Dict[str, Any]`
Creates a new user group with validation.

**Parameters:**
- `group_data`: Dictionary containing group information
  - Required fields: `group_name`, `description`
  - Optional fields: `is_active`, `created_by`

**Returns:**
```python
{
    'success': True,
    'group': {...},  # Created group record
    'operation_summary': {...},
    'message': 'Success message'
}
```

**Validation Rules:**
- Group name must be 2-100 characters long
- Group name must be unique
- Description is required

**Raises:**
- `UserGroupValidationError`: If validation fails
- `UserGroupCreateError`: If creation fails

### Read Operations

#### `read_user_group(group_id: Any) -> Dict[str, Any]`
Reads a single user group by ID with metadata.

**Parameters:**
- `group_id`: The ID of the group to read

**Returns:**
```python
{
    'success': True,
    'group': {...},  # Group record
    'metadata': {
        'total_mappings': 5,
        'active_mappings': 3,
        'last_accessed': '2025-07-29 12:00:00'
    }
}
```

#### `read_user_groups(filters: Dict[str, Any] = None, limit: int = None, offset: int = 0) -> Dict[str, Any]`
Reads multiple user groups with optional filtering and pagination.

**Parameters:**
- `filters`: Optional filters (e.g., `{'is_active': True}`)
- `limit`: Maximum number of records to return
- `offset`: Number of records to skip

**Returns:**
```python
{
    'success': True,
    'groups': [...],  # List of group records
    'metadata': {
        'total_count': 100,
        'returned_count': 25,
        'limit': 25,
        'offset': 0,
        'has_more': True
    }
}
```

### Update Operations

#### `update_user_group(group_id: Any, update_data: Dict[str, Any]) -> Dict[str, Any]`
Updates a user group with validation.

**Parameters:**
- `group_id`: The ID of the group to update
- `update_data`: Dictionary containing fields to update
  - Allowed fields: `group_name`, `description`, `is_active`, `updated_by`

**Returns:**
```python
{
    'success': True,
    'group': {...},  # Updated group record
    'changes': {...},  # Fields that were changed
    'operation_summary': {...},
    'message': 'Success message'
}
```

### Delete Operations

#### `delete_user_group_with_mappings(group_id: Any, force_delete: bool = False) -> Dict[str, Any]`
Deletes a user group and all its associated mappings.

**Parameters:**
- `group_id`: The ID of the group to delete
- `force_delete`: If True, delete even if mappings exist

**Returns:**
```python
{
    'success': True,
    'deleted_group': {...},
    'deleted_mappings_count': 5,
    'deleted_mappings': [...],
    'operation_summary': {...},
    'message': 'Success message'
}
```

#### `delete_user_group_safe(group_id: Any) -> Dict[str, Any]`
Safely deletes a user group (will not delete if mappings exist).

#### `delete_user_group_force(group_id: Any) -> Dict[str, Any]`
Force deletes a user group and all its mappings.

### Advanced Operations

#### `search_user_groups(search_term: str, search_fields: List[str] = None, limit: int = 50) -> Dict[str, Any]`
Searches user groups by name or description.

**Parameters:**
- `search_term`: Term to search for
- `search_fields`: Fields to search in (default: `['group_name', 'description']`)
- `limit`: Maximum number of results (default: 50, max: 1000)

**Returns:**
```python
{
    'success': True,
    'groups': [...],  # Sorted by relevance score
    'search_metadata': {
        'search_term': 'admin',
        'search_fields': ['group_name', 'description'],
        'total_matches': 15,
        'returned_count': 15,
        'limit_applied': False
    }
}
```

#### `bulk_update_user_groups(group_updates: List[Dict[str, Any]]) -> Dict[str, Any]`
Updates multiple user groups in a batch operation.

**Parameters:**
- `group_updates`: List of dictionaries with group_id and update data
  ```python
  [
      {'group_id': 1, 'data': {'is_active': False}},
      {'group_id': 2, 'data': {'description': 'New description'}}
  ]
  ```

**Returns:**
```python
{
    'success': True,  # True if all updates succeeded
    'total_processed': 2,
    'successful_updates': 2,
    'failed_updates': 0,
    'results': [...],  # Successful update results
    'errors': [...],   # Error details for failed updates
    'summary': {
        'success_rate': 100.0,
        'groups_updated': [1, 2],
        'groups_failed': []
    }
}
```

#### Utility Functions

#### `get_user_group_summary(group_id: Any) -> Dict[str, Any]`
Gets comprehensive summary of a user group.

#### `batch_get_group_summaries(group_ids: List[Any]) -> Dict[str, Dict[str, Any]]`
Gets summaries for multiple groups efficiently.

## Usage Examples

### Creating a User Group
```python
from system.system.database_functions.user_group_management import user_group_management as ugm

# Basic creation
group_data = {
    'group_name': 'Admin Team',
    'description': 'System administrators',
    'is_active': True,
    'created_by': 'system'
}

result = ugm.create_user_group(group_data)
print(f"Created group: {result['group']['group_name']} (ID: {result['group']['id']})")
```

### Reading Groups with Pagination
```python
# Get active groups with pagination
result = ugm.read_user_groups(
    filters={'is_active': True},
    limit=25,
    offset=0
)

print(f"Retrieved {result['metadata']['returned_count']} of {result['metadata']['total_count']} groups")

for group in result['groups']:
    print(f"- {group['group_name']}: {group['description']}")
```

### Updating a Group
```python
# Update group description and activation status
update_data = {
    'description': 'Updated description for admin team',
    'is_active': True,
    'updated_by': 'admin_user'
}

result = ugm.update_user_group(group_id=1, update_data=update_data)
print(f"Updated fields: {result['changes'].keys()}")
```

### Searching Groups
```python
# Search for groups containing "admin"
result = ugm.search_user_groups(
    search_term='admin',
    search_fields=['group_name', 'description'],
    limit=10
)

print(f"Found {result['search_metadata']['total_matches']} matching groups")
for group in result['groups']:
    print(f"- {group['group_name']} (relevance: {group['relevance_score']})")
```

### Bulk Operations
```python
# Update multiple groups at once
updates = [
    {'group_id': 1, 'data': {'is_active': False}},
    {'group_id': 2, 'data': {'description': 'Updated description'}},
    {'group_id': 3, 'data': {'group_name': 'New Name', 'is_active': True}}
]

result = ugm.bulk_update_user_groups(updates)
print(f"Success rate: {result['summary']['success_rate']}%")
print(f"Successfully updated: {result['summary']['groups_updated']}")

if result['errors']:
    print("Failed updates:")
    for error in result['errors']:
        print(f"- Group {error['group_id']}: {error['error']}")
```

### Safe vs Force Delete
```python
# Try safe delete first
try:
    result = ugm.delete_user_group_safe(group_id=1)
    print(f"Safely deleted group: {result['deleted_group']['group_name']}")
except UserGroupDeleteError as e:
    print(f"Safe delete failed: {e}")
    
    # Get summary to understand why
    summary = ugm.get_user_group_summary(group_id=1)
    if summary['mapping_summary']['active_mappings'] > 0:
        print(f"Group has {summary['mapping_summary']['active_mappings']} active mappings")
        
        # Force delete if needed
        confirm = input("Force delete? (y/N): ")
        if confirm.lower() == 'y':
            result = ugm.delete_user_group_force(group_id=1)
            print(f"Force deleted group and {result['deleted_mappings_count']} mappings")
```

## Error Handling

### Exception Hierarchy
```
DatabaseFunctionError
├── UserGroupManagementError
    ├── UserGroupValidationError    # Input validation errors
    ├── UserGroupNotFoundError      # Group doesn't exist
    ├── UserGroupCreateError        # Creation failures
    ├── UserGroupUpdateError        # Update failures
    ├── UserGroupDeleteError        # Deletion failures
    └── UserGroupMapperError        # Mapping operation failures
```

### Common Error Scenarios

#### Validation Errors
```python
try:
    ugm.create_user_group({'group_name': 'A'})  # Too short
except UserGroupValidationError as e:
    print(f"Validation error: {e}")
    # Output: Group name must be at least 2 characters long
```

#### Duplicate Names
```python
try:
    ugm.create_user_group({
        'group_name': 'Existing Group',  # Already exists
        'description': 'Test'
    })
except UserGroupValidationError as e:
    print(f"Duplicate error: {e}")
    # Output: Group with name 'Existing Group' already exists
```

#### Group Not Found
```python
try:
    ugm.read_user_group(group_id=99999)
except UserGroupNotFoundError as e:
    print(f"Not found: {e}")
    # Output: User group with ID 99999 not found
```

#### Delete Constraints
```python
try:
    ugm.delete_user_group_safe(group_id=1)
except UserGroupDeleteError as e:
    print(f"Delete error: {e}")
    # Output: Cannot delete group 'Admin Group' - it has 5 active user mappings
```

## Best Practices

### 1. Input Validation
```python
# Always validate inputs before calling functions
def create_group_from_form(form_data):
    # Validate form data first
    if not form_data.get('group_name', '').strip():
        raise ValueError("Group name is required")
    
    # Clean and prepare data
    group_data = {
        'group_name': form_data['group_name'].strip(),
        'description': form_data.get('description', '').strip(),
        'is_active': form_data.get('is_active', True),
        'created_by': get_current_user_id()
    }
    
    return ugm.create_user_group(group_data)
```

### 2. Error Handling
```python
# Use specific exception handling
try:
    result = ugm.update_user_group(group_id, update_data)
    return result
except UserGroupValidationError as e:
    # Return user-friendly validation errors
    return {'error': f"Invalid input: {e}", 'code': 'VALIDATION_ERROR'}
except UserGroupNotFoundError as e:
    # Handle missing groups
    return {'error': f"Group not found: {e}", 'code': 'NOT_FOUND'}
except UserGroupUpdateError as e:
    # Handle database errors
    logger.error(f"Database error updating group {group_id}: {e}")
    return {'error': 'Internal server error', 'code': 'SERVER_ERROR'}
```

### 3. Pagination for Large Datasets
```python
# Use pagination for large result sets
def get_all_groups_paginated():
    all_groups = []
    offset = 0
    limit = 50
    
    while True:
        result = ugm.read_user_groups(limit=limit, offset=offset)
        groups = result['groups']
        
        if not groups:
            break
            
        all_groups.extend(groups)
        
        if not result['metadata']['has_more']:
            break
            
        offset += limit
    
    return all_groups
```

### 4. Batch Operations for Performance
```python
# Use bulk operations for multiple updates
def deactivate_old_groups(group_ids):
    updates = [
        {'group_id': gid, 'data': {'is_active': False, 'updated_by': 'system'}}
        for gid in group_ids
    ]
    
    result = ugm.bulk_update_user_groups(updates)
    
    if result['failed_updates'] > 0:
        logger.warning(f"Failed to update {result['failed_updates']} groups")
        for error in result['errors']:
            logger.error(f"Group {error['group_id']}: {error['error']}")
    
    return result
```

### 5. Safe Deletion Patterns
```python
def safe_delete_with_confirmation(group_id):
    # Get group summary first
    summary = ugm.get_user_group_summary(group_id)
    group_name = summary['group']['group_name']
    
    # Check if safe deletion is possible
    if summary['mapping_summary']['can_delete_safely']:
        return ugm.delete_user_group_safe(group_id)
    
    # Inform about mappings and get confirmation
    active_mappings = summary['mapping_summary']['active_mappings']
    print(f"Group '{group_name}' has {active_mappings} active user mappings.")
    print("Deleting will remove all user associations.")
    
    confirm = input(f"Are you sure you want to delete '{group_name}'? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        return ugm.delete_user_group_force(group_id)
    else:
        return {'success': False, 'message': 'Deletion cancelled by user'}
```

## Performance Considerations

### 1. Database Connection Management
- All functions use the optimized `get_db_connection()` context manager
- Connections are automatically closed even if exceptions occur
- No connection leaks or resource waste

### 2. Query Optimization
- Single database queries where possible
- Use of `limit` clauses for single record lookups
- Efficient list comprehensions for data processing

### 3. Batch Operations
- `bulk_update_user_groups()` for multiple updates
- `batch_get_group_summaries()` for multiple group information
- Reduced database round trips

### 4. Search Optimization
- Current implementation uses in-memory search
- For production, consider:
  - Database full-text search capabilities
  - Search indexes on `group_name` and `description`
  - Elasticsearch for advanced search features

### 5. Caching Strategies
Consider implementing caching for:
- Frequently accessed group information
- Group summaries with mapping counts
- Search results for common terms

```python
# Example caching pattern (pseudo-code)
from functools import lru_cache

@lru_cache(maxsize=128, ttl=300)  # Cache for 5 minutes
def get_cached_group_summary(group_id):
    return ugm.get_user_group_summary(group_id)
```

### 6. Monitoring and Metrics
Track these metrics for optimization:
- Function execution times
- Database query performance
- Error rates by operation type
- Cache hit rates (if implemented)

## Security Considerations

### 1. Input Sanitization
- All string inputs are stripped of whitespace
- Length validation prevents buffer overflow attacks
- Field validation prevents injection attacks

### 2. Authorization
Functions don't include authorization checks - implement at the API layer:
```python
def api_create_group(user, group_data):
    # Check permissions
    if not user.has_permission('CREATE_GROUP'):
        raise PermissionError("User not authorized to create groups")
    
    # Add audit trail
    group_data['created_by'] = user.id
    
    return ugm.create_user_group(group_data)
```

### 3. Audit Logging
- All operations are logged with appropriate levels
- Include user context in API layer logging
- Log sensitive operations (deletes, bulk updates)

This comprehensive CRUD system provides a robust foundation for user group management with performance optimization, error handling, and extensibility for future enhancements.
