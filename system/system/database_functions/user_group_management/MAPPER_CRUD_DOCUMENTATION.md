# User Group Mapper CRUD Operations Documentation

## Overview
This document provides comprehensive documentation for the CRUD operations for user-group mappings (many-to-many relationships) in the Tiger ETL system.

## Table of Contents
- [Function Reference](#function-reference)
- [Usage Examples](#usage-examples)
- [Advanced Operations](#advanced-operations)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Function Reference

### Core CRUD Operations

#### `create_user_group_mapping(mapper_data: Dict[str, Any]) -> Dict[str, Any]`
Creates a new user-group mapping with validation.

**Parameters:**
- `mapper_data`: Dictionary containing mapping information
  - Required fields: `user_id`, `group_id`
  - Optional fields: `is_active`, `created_by`, `notes`

**Returns:**
```python
{
    'success': True,
    'mapping': {...},  # Created mapping record
    'operation_summary': {
        'mapping_id': 123,
        'user_id': 456,
        'group_id': 789,
        'is_active': True,
        'created_at': '2025-07-29 12:00:00'
    },
    'message': 'Success message'
}
```

**Validation Rules:**
- user_id and group_id must be positive integers
- Group must exist in the database
- Duplicate mappings are prevented

**Raises:**
- `UserGroupValidationError`: If validation fails
- `UserGroupMapperError`: If creation fails

#### `read_user_group_mapping(mapping_id: Any) -> Dict[str, Any]`
Reads a single user-group mapping by ID.

**Parameters:**
- `mapping_id`: The ID of the mapping to read

**Returns:**
```python
{
    'success': True,
    'mapping': {...},  # Mapping record
    'group_info': {
        'group_name': 'Admin Group',
        'group_description': 'System administrators',
        'group_is_active': True
    },
    'metadata': {
        'is_active': True,
        'created_at': '2025-07-29 12:00:00',
        'updated_at': '2025-07-29 13:00:00',
        'has_notes': True
    }
}
```

#### `read_user_group_mappings(filters: Dict[str, Any] = None, limit: int = None, offset: int = 0) -> Dict[str, Any]`
Reads multiple user-group mappings with optional filtering and pagination.

**Parameters:**
- `filters`: Optional filters (e.g., `{'user_id': 123, 'is_active': True}`)
- `limit`: Maximum number of records to return
- `offset`: Number of records to skip

**Returns:**
```python
{
    'success': True,
    'mappings': [...],  # List of mapping records with group info
    'metadata': {
        'total_count': 100,
        'returned_count': 25,
        'limit': 25,
        'offset': 0,
        'has_more': True,
        'active_count': 20,
        'inactive_count': 5
    }
}
```

#### `update_user_group_mapping(mapping_id: Any, update_data: Dict[str, Any]) -> Dict[str, Any]`
Updates a user-group mapping with validation.

**Parameters:**
- `mapping_id`: The ID of the mapping to update
- `update_data`: Dictionary containing fields to update
  - Allowed fields: `is_active`, `updated_by`, `notes`

**Returns:**
```python
{
    'success': True,
    'mapping': {...},  # Updated mapping record
    'changes': {...},  # Fields that were changed
    'operation_summary': {
        'mapping_id': 123,
        'user_id': 456,
        'group_id': 789,
        'fields_updated': ['is_active', 'notes'],
        'updated_at': '2025-07-29 13:00:00',
        'was_active': True,
        'now_active': False
    },
    'message': 'Success message'
}
```

#### `delete_user_group_mapping(mapping_id: Any) -> Dict[str, Any]`
Deletes a user-group mapping (hard delete).

**Parameters:**
- `mapping_id`: The ID of the mapping to delete

**Returns:**
```python
{
    'success': True,
    'deleted_mapping': {...},
    'operation_summary': {
        'mapping_id': 123,
        'user_id': 456,
        'group_id': 789,
        'group_name': 'Admin Group',
        'was_active': True,
        'deleted_at': '2025-07-29 13:00:00'
    },
    'message': 'Success message'
}
```

### Advanced Operations

#### `get_user_group_mappings_by_user(user_id: Any, include_inactive: bool = False) -> Dict[str, Any]`
Gets all group mappings for a specific user.

**Parameters:**
- `user_id`: The user ID to get mappings for
- `include_inactive`: Whether to include inactive mappings (default: False)

**Returns:**
```python
{
    'success': True,
    'user_id': 456,
    'mappings': [...],  # List of user's group mappings
    'summary': {
        'total_mappings': 5,
        'active_mappings': 3,
        'inactive_mappings': 2,
        'group_names': ['Admin Group', 'Users Group', 'Editors Group'],
        'group_count': 3
    }
}
```

#### `get_group_user_mappings(group_id: Any, include_inactive: bool = False) -> Dict[str, Any]`
Gets all user mappings for a specific group.

**Parameters:**
- `group_id`: The group ID to get mappings for
- `include_inactive`: Whether to include inactive mappings (default: False)

**Returns:**
```python
{
    'success': True,
    'group': {...},  # Group record
    'mappings': [...],  # List of group's user mappings
    'summary': {
        'total_mappings': 10,
        'active_mappings': 8,
        'inactive_mappings': 2,
        'user_ids': [123, 456, 789, ...],
        'unique_users': 8
    }
}
```

#### `bulk_create_user_group_mappings(mappings_data: List[Dict[str, Any]]) -> Dict[str, Any]`
Creates multiple user-group mappings in batch.

**Parameters:**
- `mappings_data`: List of mapping dictionaries (max 1000)
  ```python
  [
      {'user_id': 123, 'group_id': 456},
      {'user_id': 124, 'group_id': 456, 'notes': 'Special access'},
      ...
  ]
  ```

**Returns:**
```python
{
    'success': True,  # True if all succeeded
    'total_processed': 100,
    'successful_creations': 95,
    'failed_creations': 2,
    'skipped_duplicates': 3,
    'results': [...],  # Successful creations
    'errors': [...],   # Failed creations with reasons
    'skipped': [...],  # Skipped duplicates
    'summary': {
        'success_rate': 95.0,
        'created_mappings': [(123, 456), (124, 456), ...],
        'failed_mappings': [(125, 999), ...]
    }
}
```

#### `bulk_update_user_group_mappings(mapping_updates: List[Dict[str, Any]]) -> Dict[str, Any]`
Updates multiple user-group mappings in batch.

**Parameters:**
- `mapping_updates`: List of update dictionaries (max 100)
  ```python
  [
      {'mapping_id': 1, 'data': {'is_active': False}},
      {'mapping_id': 2, 'data': {'notes': 'Updated access level'}},
      ...
  ]
  ```

#### `deactivate_user_from_group(user_id: Any, group_id: Any) -> Dict[str, Any]`
Deactivates a user from a group (soft delete).

**Parameters:**
- `user_id`: The user ID
- `group_id`: The group ID

**Returns:**
```python
{
    'success': True,
    'deactivated_mapping': {...},
    'operation_summary': {
        'user_id': 123,
        'group_id': 456,
        'mapping_id': 789,
        'action': 'deactivated'
    },
    'message': 'Success message'
}
```

#### `activate_user_in_group(user_id: Any, group_id: Any) -> Dict[str, Any]`
Activates a user in a group (reactivates existing or creates new).

**Parameters:**
- `user_id`: The user ID
- `group_id`: The group ID

**Returns:**
```python
{
    'success': True,
    'action': 'reactivated',  # 'reactivated', 'created', or 'already_active'
    'mapping': {...},
    'operation_summary': {
        'user_id': 123,
        'group_id': 456,
        'mapping_id': 789,
        'action': 'reactivated'
    },
    'message': 'Success message'
}
```

## Usage Examples

### Creating User-Group Mappings
```python
from system.system.database_functions.user_group_management import user_group_management as ugm

# Basic mapping creation
mapping_data = {
    'user_id': 123,
    'group_id': 456,
    'is_active': True,
    'created_by': 'admin',
    'notes': 'Initial access grant'
}

result = ugm.create_user_group_mapping(mapping_data)
print(f"Created mapping: User {result['mapping']['user_id']} -> Group {result['mapping']['group_id']}")
```

### Reading User's Groups
```python
# Get all active groups for a user
result = ugm.get_user_group_mappings_by_user(user_id=123, include_inactive=False)

print(f"User {result['user_id']} is in {result['summary']['active_mappings']} groups:")
for group_name in result['summary']['group_names']:
    print(f"  - {group_name}")
```

### Reading Group Members
```python
# Get all active users in a group
result = ugm.get_group_user_mappings(group_id=456, include_inactive=False)

print(f"Group '{result['group']['group_name']}' has {result['summary']['active_mappings']} members:")
for mapping in result['mappings']:
    if mapping.get('is_active', True):
        print(f"  - User ID: {mapping['user_id']}")
```

### Bulk Operations
```python
# Bulk create mappings
mappings_to_create = [
    {'user_id': 101, 'group_id': 1},
    {'user_id': 102, 'group_id': 1},
    {'user_id': 103, 'group_id': 1},
    {'user_id': 101, 'group_id': 2},
    {'user_id': 102, 'group_id': 2}
]

result = ugm.bulk_create_user_group_mappings(mappings_to_create)
print(f"Created {result['successful_creations']} of {result['total_processed']} mappings")
print(f"Skipped {result['skipped_duplicates']} duplicates")

if result['errors']:
    print("Failed creations:")
    for error in result['errors']:
        print(f"  - User {error['user_id']} -> Group {error['group_id']}: {error['error']}")
```

### Soft Delete (Deactivation)
```python
# Deactivate user from group (soft delete)
result = ugm.deactivate_user_from_group(user_id=123, group_id=456)
print(f"Deactivated: {result['message']}")

# Reactivate user in group
result = ugm.activate_user_in_group(user_id=123, group_id=456)
print(f"Action taken: {result['action']}")
print(f"Result: {result['message']}")
```

### Filtering and Pagination
```python
# Get mappings with filters and pagination
result = ugm.read_user_group_mappings(
    filters={'is_active': True, 'group_id': 456},
    limit=25,
    offset=0
)

print(f"Active mappings for group 456: {result['metadata']['returned_count']}")
print(f"Total: {result['metadata']['total_count']}, Has more: {result['metadata']['has_more']}")

for mapping in result['mappings']:
    print(f"  - User {mapping['user_id']}: {mapping.get('notes', 'No notes')}")
```

### Update Operations
```python
# Update mapping status and notes
mapping_id = 123
update_data = {
    'is_active': False,
    'notes': 'Access temporarily suspended',
    'updated_by': 'admin'
}

result = ugm.update_user_group_mapping(mapping_id, update_data)
print(f"Updated fields: {result['changes'].keys()}")
print(f"Status changed from {result['operation_summary']['was_active']} to {result['operation_summary']['now_active']}")
```

## Error Handling

### Exception Types
- `UserGroupValidationError`: Input validation failures
- `UserGroupMapperError`: Mapping operation failures
- `UserGroupNotFoundError`: Referenced group doesn't exist

### Common Error Scenarios

#### Validation Errors
```python
try:
    ugm.create_user_group_mapping({'user_id': 'invalid'})
except UserGroupValidationError as e:
    print(f"Validation error: {e}")
    # Output: User ID must be a valid integer: invalid literal...
```

#### Duplicate Mappings
```python
try:
    ugm.create_user_group_mapping({'user_id': 123, 'group_id': 456})  # Already exists
except UserGroupValidationError as e:
    print(f"Duplicate error: {e}")
    # Output: Mapping already exists between user 123 and group 456
```

#### Mapping Not Found
```python
try:
    ugm.read_user_group_mapping(mapping_id=99999)
except UserGroupMapperError as e:
    print(f"Not found: {e}")
    # Output: User-group mapping with ID 99999 not found
```

#### Group Not Found
```python
try:
    ugm.create_user_group_mapping({'user_id': 123, 'group_id': 99999})
except UserGroupNotFoundError as e:
    print(f"Group not found: {e}")
    # Output: User group with ID 99999 not found
```

## Best Practices

### 1. Input Validation
```python
def add_user_to_group_safely(user_id, group_id, created_by):
    """Add user to group with comprehensive validation."""
    try:
        # Validate inputs
        if not user_id or not group_id:
            raise ValueError("User ID and Group ID are required")
        
        # Check if mapping already exists
        existing = ugm.get_user_group_mappings_by_user(user_id)
        user_groups = [m['group_id'] for m in existing['mappings'] if m.get('is_active', True)]
        
        if group_id in user_groups:
            return {'success': False, 'message': 'User already in group'}
        
        # Create mapping
        mapping_data = {
            'user_id': user_id,
            'group_id': group_id,
            'created_by': created_by,
            'notes': f'Added by {created_by}'
        }
        
        return ugm.create_user_group_mapping(mapping_data)
        
    except (UserGroupValidationError, UserGroupMapperError, UserGroupNotFoundError) as e:
        return {'success': False, 'error': str(e)}
```

### 2. Batch Operations
```python
def sync_user_groups(user_id, target_group_ids):
    """Synchronize user's group memberships."""
    # Get current mappings
    current = ugm.get_user_group_mappings_by_user(user_id, include_inactive=False)
    current_group_ids = {m['group_id'] for m in current['mappings']}
    
    target_group_ids = set(target_group_ids)
    
    # Calculate changes
    to_add = target_group_ids - current_group_ids
    to_remove = current_group_ids - target_group_ids
    
    results = {'added': [], 'removed': [], 'errors': []}
    
    # Add new memberships
    if to_add:
        mappings_to_create = [{'user_id': user_id, 'group_id': gid} for gid in to_add]
        create_result = ugm.bulk_create_user_group_mappings(mappings_to_create)
        results['added'] = create_result['results']
        results['errors'].extend(create_result['errors'])
    
    # Remove old memberships (deactivate)
    for group_id in to_remove:
        try:
            deactivate_result = ugm.deactivate_user_from_group(user_id, group_id)
            results['removed'].append(deactivate_result)
        except Exception as e:
            results['errors'].append({'group_id': group_id, 'error': str(e)})
    
    return results
```

### 3. Soft Delete Pattern
```python
def manage_user_access(user_id, group_id, action='activate'):
    """Manage user access with soft delete pattern."""
    try:
        if action == 'activate':
            result = ugm.activate_user_in_group(user_id, group_id)
            return {'success': True, 'action': result['action'], 'message': result['message']}
            
        elif action == 'deactivate':
            result = ugm.deactivate_user_from_group(user_id, group_id)
            return {'success': True, 'action': 'deactivated', 'message': result['message']}
            
        else:
            return {'success': False, 'error': 'Invalid action. Use "activate" or "deactivate"'}
            
    except UserGroupMapperError as e:
        if 'No active mapping found' in str(e):
            return {'success': False, 'error': 'User is not currently in this group'}
        else:
            return {'success': False, 'error': str(e)}
```

### 4. Audit and Monitoring
```python
def audit_user_group_changes(user_id, action_by):
    """Audit user group membership changes."""
    try:
        result = ugm.get_user_group_mappings_by_user(user_id, include_inactive=True)
        
        # Log current state
        logger.info(f"User {user_id} group audit by {action_by}:")
        logger.info(f"  Total mappings: {result['summary']['total_mappings']}")
        logger.info(f"  Active groups: {result['summary']['active_mappings']}")
        logger.info(f"  Group names: {', '.join(result['summary']['group_names'])}")
        
        # Check for recent changes
        recent_changes = []
        for mapping in result['mappings']:
            updated_at = mapping.get('updated_on')
            if updated_at:
                # Check if updated in last 24 hours (implement date logic)
                recent_changes.append(mapping)
        
        if recent_changes:
            logger.info(f"  Recent changes: {len(recent_changes)} mappings modified")
        
        return result
        
    except Exception as e:
        logger.error(f"Audit failed for user {user_id}: {e}")
        return None
```

### 5. Performance Optimization
```python
def get_user_groups_optimized(user_ids):
    """Get groups for multiple users efficiently."""
    if len(user_ids) > 100:
        # Process in chunks
        results = {}
        for i in range(0, len(user_ids), 100):
            chunk = user_ids[i:i+100]
            chunk_results = get_user_groups_optimized(chunk)
            results.update(chunk_results)
        return results
    
    # Single batch operation
    all_mappings = ugm.read_user_group_mappings(
        filters={'user_id__in': user_ids, 'is_active': True}  # Hypothetical IN filter
    )
    
    # Group by user_id
    user_groups = {}
    for mapping in all_mappings['mappings']:
        user_id = mapping['user_id']
        if user_id not in user_groups:
            user_groups[user_id] = []
        user_groups[user_id].append(mapping)
    
    return user_groups
```

## Performance Considerations

### 1. Database Optimization
- Use indexes on `user_id`, `group_id`, and `is_active` columns
- Consider composite indexes for common query patterns
- Use pagination for large result sets

### 2. Batch Operations
- Use bulk operations for multiple mappings
- Limit batch sizes (1000 for creates, 100 for updates)
- Handle partial failures gracefully

### 3. Caching Strategies
- Cache frequently accessed user-group relationships
- Implement cache invalidation on mapping changes
- Use Redis for session-based group membership caching

### 4. Query Patterns
- Use `include_inactive=False` when possible to reduce data transfer
- Filter at database level rather than in application code
- Use appropriate limits for UI pagination

This comprehensive mapper CRUD system provides robust functionality for managing user-group relationships with performance optimization, error handling, and extensibility for enterprise applications.
