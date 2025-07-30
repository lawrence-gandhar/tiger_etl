"""User group management database functions.

This module contains optimized database functions for managing user groups,
including creation, deletion, and relationship management with proper
transaction handling and error management.
"""

import logging
from typing import Dict, Any, List, Tuple
from contextlib import contextmanager

from sqlalchemy.orm import Session
from system.system.database_connections.pg_db import get_session, PostgresDB
from system.system.database_connections.exceptions import (
    SQLAlchemyDeleteError,
    SQLAlchemyReadError,
    SQLAlchemyInsertError,
    SQLAlchemyUpdateError,
)
from system.system.database_functions.exceptions import (
    UserGroupDeleteError,
    UserGroupNotFoundError,
    UserGroupValidationError,
    UserGroupMapperError,
    UserGroupCreateError,
    UserGroupUpdateError,
)
from system.system.database_functions.user_group_management.validations import (
    validate_group_create_data,
    validate_group_update_data,
    validate_group_filters,
    validate_pagination_params,
    validate_search_params,
    validate_mapping_create_data,
    validate_mapping_update_data,
    validate_bulk_mapping_create_data,
    validate_user_group_activation,
    validate_positive_integer,
)
from system.system.constants.model_constants.user_group_management_constants import (
    USER_GROUPS_TABLE,
    USER_GROUP_MAPPER_TABLE,
    MAPPING_ID_POSITIVE_ERROR,
    MAPPING_ID_INTEGER_ERROR,
)

# Set up logging
logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """Context manager for SQLAlchemy session with automatic cleanup.

    Yields:
        Session: SQLAlchemy session instance

    Ensures:
        Session is properly closed even if an exception occurs
    """
    session: Session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def validate_group_id(group_id: Any) -> int:
    """Validate group ID parameter.
    
    Args:
        group_id: The group ID to validate
        
    Returns:
        int: Validated group ID
        
    Raises:
        UserGroupValidationError: If group ID is invalid
    """
    if group_id is None:
        raise UserGroupValidationError("Group ID cannot be None")
    
    try:
        group_id = int(group_id)
    except (ValueError, TypeError) as e:
        raise UserGroupValidationError(f"Group ID must be a valid integer: {e}") from e
    
    if group_id <= 0:
        raise UserGroupValidationError("Group ID must be a positive integer")
    
    return group_id


def check_group_exists(db_instance: Any, group_id: int) -> Dict[str, Any]:
    """Check if a user group exists in the database.
    
    Args:
        db_instance: PostgresDB instance
        group_id: The group ID to check
        
    Returns:
        Dict[str, Any]: Group record if found
        
    Raises:
        UserGroupNotFoundError: If group doesn't exist
        UserGroupValidationError: If validation fails
    """
    try:
        # Read the group record with optimized query
        group_records = db_instance.read(
            table_name=USER_GROUPS_TABLE,
            conditions={'id': group_id},
            limit=1  # Optimize: only need one record
        )
        
        if not group_records:
            raise UserGroupNotFoundError(f"User group with ID {group_id} not found")
        
        # Convert record to dictionary for easier handling
        group_record = dict(group_records[0]._mapping)
        logger.debug(f"Found user group: {group_record['group_name']} (ID: {group_id})")
        
        return group_record
        
    except SQLAlchemyReadError as e:
        raise UserGroupValidationError(f"Failed to validate group existence: {e}") from e


def get_group_mappings(db_instance: PostgresDB, group_id: int) -> List[Dict[str, Any]]:
    """Get all user mappings for a group with optimized query.
    
    Args:
        db_instance: PostgresDB instance
        group_id: The group ID to get mappings for
        
    Returns:
        List[Dict[str, Any]]: List of mapping records
        
    Raises:
        UserGroupMapperError: If failed to retrieve mappings
    """
    try:
        # Get all mappings for this group - optimized with indexed query
        mapping_records = db_instance.read(
            table_name=USER_GROUP_MAPPER_TABLE,
            conditions={'group_id': group_id}
        )
        
        # Convert to list of dictionaries with optimized list comprehension
        mappings = [dict(record._mapping) for record in mapping_records]
        
        logger.debug(f"Found {len(mappings)} user mappings for group {group_id}")
        
        return mappings
        
    except SQLAlchemyReadError as e:
        raise UserGroupMapperError(f"Failed to retrieve group mappings: {e}") from e


def get_group_with_mappings(group_id: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Get group and its mappings in a single optimized operation.
    
    Args:
        group_id: The group ID to retrieve
        
    Returns:
        Tuple[Dict[str, Any], List[Dict[str, Any]]]: Group record and mappings
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupNotFoundError: If group doesn't exist
    """
    with get_db_connection() as db:
        # Validate group ID once
        validated_group_id = validate_group_id(group_id)
        
        # Get both group and mappings efficiently
        group_record = check_group_exists(db, validated_group_id)
        mappings = get_group_mappings(db, validated_group_id)
        
        return group_record, mappings


# =============================================================================
# CRUD OPERATIONS FOR USER GROUPS
# =============================================================================

def create_user_group(group_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user group with validation.
    
    Args:
        group_data: Dictionary containing group information
                   Required fields: group_name, description
                   Optional fields: is_active, created_by
    
    Returns:
        Dict[str, Any]: Created group record with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupCreateError: If creation fails
    """
    # Validate data using Pydantic
    validated_data = validate_group_create_data(group_data)
    
    try:
        with get_db_connection() as db:
            # Check for duplicate group name
            existing_groups = db.read(
                table_name=USER_GROUPS_TABLE,
                conditions={'group_name': validated_data['group_name']},
                limit=1
            )
            
            if existing_groups:
                raise UserGroupValidationError(
                    f"Group with name '{validated_data['group_name']}' already exists"
                )
            
            # Create the group
            created_records = db.create(
                table_name=USER_GROUPS_TABLE,
                data=validated_data
            )
            
            if not created_records:
                raise UserGroupCreateError("Failed to create group - no records returned")
            
            created_group = dict(created_records[0]._mapping)
            
            logger.info(f"Successfully created user group: {created_group['group_name']} (ID: {created_group['id']})")
            
            return {
                'success': True,
                'group': created_group,
                'operation_summary': {
                    'group_id': created_group['id'],
                    'group_name': created_group['group_name'],
                    'is_active': created_group.get('is_active', True),
                    'created_at': str(created_group.get('created_on'))
                },
                'message': f"Successfully created group '{created_group['group_name']}'"
            }
            
    except SQLAlchemyInsertError as e:
        logger.error(f"Database error creating group: {e}")
        raise UserGroupCreateError(f"Failed to create group: {e}") from e
    except (UserGroupValidationError, UserGroupCreateError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating group: {e}")
        raise UserGroupCreateError(f"Unexpected error during group creation: {e}") from e


def read_user_group(group_id: Any) -> Dict[str, Any]:
    """Read a single user group by ID with optimized query.
    
    Args:
        group_id: The ID of the group to read
        
    Returns:
        Dict[str, Any]: Group record with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupNotFoundError: If group doesn't exist
    """
    try:
        # Use existing optimized function
        group_record, mappings = get_group_with_mappings(group_id)
        
        return {
            'success': True,
            'group': group_record,
            'metadata': {
                'total_mappings': len(mappings),
                'active_mappings': len([m for m in mappings if m.get('is_active', True)]),
                'last_accessed': str(group_record.get('updated_on', group_record.get('created_on')))
            }
        }
        
    except (UserGroupValidationError, UserGroupNotFoundError) as e:
        logger.error(f"Failed to read group: {e}")
        raise


def read_user_groups(filters: Dict[str, Any] = None, limit: int = None, offset: int = 0) -> Dict[str, Any]:
    """Read multiple user groups with optional filtering and pagination.
    
    Args:
        filters: Optional filters to apply (e.g., {'is_active': True})
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        Dict[str, Any]: List of group records with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    # Validate pagination parameters using Pydantic
    validated_pagination = validate_pagination_params(limit=limit, offset=offset)
    
    # Validate filters using Pydantic if provided
    validated_filters = {}
    if filters:
        validated_filters = validate_group_filters(filters)
    
    try:
        with get_db_connection() as db:
            # Read groups with pagination
            groups = db.read(
                table_name=USER_GROUPS_TABLE,
                conditions=validated_filters,
                limit=validated_pagination.get('limit'),
                offset=validated_pagination.get('offset', 0)
            )
            
            # Convert to list of dictionaries
            group_records = [dict(group._mapping) for group in groups]
            
            # Get total count for pagination metadata
            total_count = len(db.read(
                table_name=USER_GROUPS_TABLE,
                conditions=validated_filters
            ))
            
            logger.debug(f"Retrieved {len(group_records)} user groups (total: {total_count})")
            
            return {
                'success': True,
                'groups': group_records,
                'metadata': {
                    'total_count': total_count,
                    'returned_count': len(group_records),
                    'limit': validated_pagination.get('limit'),
                    'offset': validated_pagination.get('offset', 0),
                    'has_more': (
                        validated_pagination.get('limit') and 
                        (validated_pagination.get('offset', 0) + len(group_records)) < total_count
                    )
                }
            }
            
    except SQLAlchemyReadError as e:
        raise UserGroupValidationError(f"Database error reading groups: {e}") from e
    except Exception as e:
        raise UserGroupValidationError(f"Unexpected error reading groups: {e}") from e


def _validate_update_data(update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and process update data for user groups.
    
    Args:
        update_data: Raw update data
        
    Returns:
        Dict[str, Any]: Processed and validated update data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    if not update_data:
        raise UserGroupValidationError("Update data cannot be empty")
    
    # Define allowed fields for update
    allowed_fields = {'group_name', 'description', 'is_active', 'updated_by'}
    invalid_fields = set(update_data.keys()) - allowed_fields
    
    if invalid_fields:
        raise UserGroupValidationError(
            f"Invalid fields for update: {', '.join(invalid_fields)}. "
            f"Allowed fields: {', '.join(allowed_fields)}"
        )
    
    processed_data = {}
    
    # Validate group_name
    if 'group_name' in update_data:
        group_name = update_data['group_name'].strip()
        if not group_name or len(group_name) < 2:
            raise UserGroupValidationError("Group name must be at least 2 characters long")
        if len(group_name) > 100:
            raise UserGroupValidationError("Group name cannot exceed 100 characters")
        processed_data['group_name'] = group_name
    
    # Validate description
    if 'description' in update_data:
        processed_data['description'] = update_data['description'].strip()
    
    # Process other fields
    if 'is_active' in update_data:
        processed_data['is_active'] = bool(update_data['is_active'])
    
    if 'updated_by' in update_data:
        processed_data['updated_by'] = update_data['updated_by']
    
    return processed_data


def _check_group_name_uniqueness(db_instance: PostgresDB, group_name: str, 
                                exclude_group_id: int = None) -> None:
    """Check if group name is unique.
    
    Args:
        db_instance: Database instance
        group_name: Group name to check
        exclude_group_id: Group ID to exclude from check (for updates)
        
    Raises:
        UserGroupValidationError: If name is not unique
    """
    existing_with_name = db_instance.read(
        table_name=USER_GROUPS_TABLE,
        conditions={'group_name': group_name},
        limit=1
    )
    
    if existing_with_name:
        existing_id = existing_with_name[0].id
        if exclude_group_id is None or existing_id != exclude_group_id:
            raise UserGroupValidationError(
                f"Group with name '{group_name}' already exists"
            )


def update_user_group(group_id: Any, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a user group with validation.
    
    Args:
        group_id: The ID of the group to update
        update_data: Dictionary containing fields to update
    
    Returns:
        Dict[str, Any]: Updated group record with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupNotFoundError: If group doesn't exist
        UserGroupUpdateError: If update fails
    """
    # Validate inputs using Pydantic
    validated_group_id = validate_positive_integer(group_id, "Group ID")
    validated_update_data = validate_group_update_data(update_data)
    
    try:
        with get_db_connection() as db:
            # Check if group exists
            existing_group = check_group_exists(db, validated_group_id)
            
            # Check for duplicate group name if name is being updated
            if 'group_name' in validated_update_data:
                _check_group_name_uniqueness(
                    db, validated_update_data['group_name'], validated_group_id
                )
            
            # Perform update
            updated_records = db.update(
                table_name=USER_GROUPS_TABLE,
                conditions={'id': validated_group_id},
                data=validated_update_data
            )
            
            if not updated_records:
                raise UserGroupUpdateError(
                    f"Failed to update group {validated_group_id} - no records affected"
                )
            
            updated_group = dict(updated_records[0]._mapping)
            
            logger.info(f"Successfully updated user group: {updated_group['group_name']} (ID: {validated_group_id})")
            
            return {
                'success': True,
                'group': updated_group,
                'changes': validated_update_data,
                'operation_summary': {
                    'group_id': validated_group_id,
                    'group_name': updated_group['group_name'],
                    'fields_updated': list(validated_update_data.keys()),
                    'updated_at': str(updated_group.get('updated_on')),
                    'was_active': existing_group.get('is_active'),
                    'now_active': updated_group.get('is_active')
                },
                'message': f"Successfully updated group '{updated_group['group_name']}'"
            }
            
    except SQLAlchemyUpdateError as e:
        raise UserGroupUpdateError(f"Database error updating group: {e}") from e
    except (UserGroupValidationError, UserGroupNotFoundError, UserGroupUpdateError):
        raise
    except Exception as e:
        raise UserGroupUpdateError(f"Unexpected error updating group: {e}") from e


# =============================================================================
# ADVANCED CRUD OPERATIONS
# =============================================================================

def _validate_search_params(search_term: str, search_fields: List[str], limit: int) -> Tuple[str, List[str], int]:
    """Validate search parameters.
    
    Args:
        search_term: Term to search for
        search_fields: Fields to search in
        limit: Maximum results
        
    Returns:
        Tuple of validated parameters
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    if not search_term or not search_term.strip():
        raise UserGroupValidationError("Search term cannot be empty")
    
    clean_search_term = search_term.strip().lower()
    
    validated_fields = search_fields if search_fields else ['group_name', 'description']
    
    if limit <= 0 or limit > 1000:
        raise UserGroupValidationError("Limit must be between 1 and 1000")
    
    return clean_search_term, validated_fields, limit


def _calculate_relevance_score(group_dict: Dict[str, Any], search_term: str, 
                             search_fields: List[str]) -> int:
    """Calculate relevance score for a group record.
    
    Args:
        group_dict: Group record as dictionary
        search_term: Search term (already cleaned)
        search_fields: Fields to search in
        
    Returns:
        int: Relevance score (0 means no match)
    """
    relevance_score = 0
    
    for field in search_fields:
        field_value = str(group_dict.get(field, '')).lower()
        if search_term in field_value:
            # Simple scoring: exact match = 2, contains = 1
            if field_value == search_term:
                relevance_score += 2
            else:
                relevance_score += 1
    
    return relevance_score


def search_user_groups(search_term: str, search_fields: List[str] = None, 
                      limit: int = 50) -> Dict[str, Any]:
    """Search user groups by name or description with optimized query.
    
    Args:
        search_term: Term to search for
        search_fields: Fields to search in (default: ['group_name', 'description'])
        limit: Maximum number of results (default: 50)
        
    Returns:
        Dict[str, Any]: Search results with relevance scoring
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    # Validate parameters using Pydantic
    if search_fields is None:
        search_fields = ['group_name', 'description']
    
    validated_params = validate_search_params(search_term, search_fields, limit)
    
    try:
        with get_db_connection() as db:
            # Get all groups (in production, use database search functions)
            all_groups = db.read(table_name=USER_GROUPS_TABLE)
            
            # Process search results
            matching_groups = []
            
            for group in all_groups:
                group_dict = dict(group._mapping)
                relevance_score = _calculate_relevance_score(
                    group_dict, validated_params['search_term'], validated_params['search_fields']
                )
                
                if relevance_score > 0:
                    group_dict['relevance_score'] = relevance_score
                    matching_groups.append(group_dict)
            
            # Sort by relevance and limit results
            matching_groups.sort(key=lambda x: x['relevance_score'], reverse=True)
            limited_results = matching_groups[:validated_params['limit']]
            
            logger.debug(f"Search for '{search_term}' returned {len(limited_results)} results")
            
            return {
                'success': True,
                'groups': limited_results,
                'search_metadata': {
                    'search_term': validated_params['search_term'],
                    'search_fields': validated_params['search_fields'],
                    'total_matches': len(matching_groups),
                    'returned_count': len(limited_results),
                    'limit_applied': len(matching_groups) > validated_params['limit']
                }
            }
            
    except SQLAlchemyReadError as e:
        raise UserGroupValidationError(f"Database error during search: {e}") from e
    except Exception as e:
        raise UserGroupValidationError(f"Unexpected error during search: {e}") from e


def bulk_update_user_groups(group_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update multiple user groups in an optimized batch operation.
    
    Args:
        group_updates: List of dictionaries with 'group_id' and update data
                      Format: [{'group_id': 1, 'data': {'is_active': False}}, ...]
    
    Returns:
        Dict[str, Any]: Summary of bulk update operation
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    if not group_updates:
        raise UserGroupValidationError("Group updates list cannot be empty")
    
    if len(group_updates) > 100:
        raise UserGroupValidationError("Cannot update more than 100 groups at once")
    
    results = []
    errors = []
    
    # Process each update
    for i, update_item in enumerate(group_updates):
        try:
            if 'group_id' not in update_item or 'data' not in update_item:
                raise UserGroupValidationError(
                    f"Item {i}: Missing 'group_id' or 'data' field"
                )
            
            result = update_user_group(
                group_id=update_item['group_id'],
                update_data=update_item['data']
            )
            results.append({
                'group_id': update_item['group_id'],
                'success': True,
                'result': result
            })
            
        except (UserGroupValidationError, UserGroupNotFoundError, UserGroupUpdateError) as e:
            error_info = {
                'group_id': update_item.get('group_id', 'unknown'),
                'success': False,
                'error': str(e)
            }
            errors.append(error_info)
            logger.warning(f"Failed to update group {update_item.get('group_id')}: {e}")
    
    return {
        'success': len(errors) == 0,
        'total_processed': len(group_updates),
        'successful_updates': len(results),
        'failed_updates': len(errors),
        'results': results,
        'errors': errors,
        'summary': {
            'success_rate': len(results) / len(group_updates) * 100 if group_updates else 0,
            'groups_updated': [r['group_id'] for r in results],
            'groups_failed': [e['group_id'] for e in errors]
        }
    }


def delete_user_group_with_mappings(group_id: Any, force_delete: bool = False) -> Dict[str, Any]:
    """Delete a user group and all its associated mappings with optimized operations.
    
    This function performs a transactional delete operation:
    1. Validates the group ID
    2. Checks if the group exists and gets mappings in one database connection
    3. Validates deletion constraints
    4. Performs batch deletion operations
    5. Returns comprehensive operation summary
    
    Args:
        group_id: The ID of the group to delete
        force_delete: If True, delete even if mappings exist (default: False)
        
    Returns:
        Dict[str, Any]: Summary of the deletion operation
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupNotFoundError: If group doesn't exist
        UserGroupDeleteError: If deletion fails
    """
    try:
        # Step 1 & 2: Validate and get group with mappings in optimized single connection
        group_record, mappings = get_group_with_mappings(group_id)
        validated_group_id = int(group_id)  # Already validated in get_group_with_mappings
        
        logger.info(f"Starting deletion process for group: {group_record['group_name']} (ID: {validated_group_id})")
        
        # Step 3: Optimized constraint validation
        active_mappings = [m for m in mappings if m.get('is_active', True)]
        
        if active_mappings and not force_delete:
            raise UserGroupDeleteError(
                f"Cannot delete group '{group_record['group_name']}' - it has {len(active_mappings)} "
                f"active user mappings. Use force_delete=True to override."
            )
        
        # Step 4: Perform deletions with optimized database operations
        with get_db_connection() as db:
            deleted_mappings = []
            
            # Batch delete mappings if they exist
            if mappings:
                logger.info(f"Deleting {len(mappings)} user mappings for group {validated_group_id}")
                
                # Optimize: collect all mapping IDs for potential batch operations
                mapping_ids = [mapping['id'] for mapping in mappings]
                
                # Delete mappings individually (can be optimized to batch delete if supported)
                for mapping_id in mapping_ids:
                    try:
                        deleted_mapping = db.delete(
                            table_name=USER_GROUP_MAPPER_TABLE,
                            conditions={'id': mapping_id}
                        )
                        deleted_mappings.extend(deleted_mapping)
                        
                    except SQLAlchemyDeleteError as e:
                        raise UserGroupMapperError(
                            f"Failed to delete mapping {mapping_id}: {e}"
                        ) from e
                
                logger.info(f"Successfully deleted {len(deleted_mappings)} user mappings")
            
            # Delete the group record
            logger.info(f"Deleting user group: {group_record['group_name']} (ID: {validated_group_id})")
            
            deleted_group_records = db.delete(
                table_name=USER_GROUPS_TABLE,
                conditions={'id': validated_group_id}
            )
            
            if not deleted_group_records:
                raise UserGroupDeleteError(
                    f"Failed to delete group {validated_group_id} - no records affected"
                )
            
            deleted_group = dict(deleted_group_records[0]._mapping)
            
            logger.info(f"Successfully deleted user group: {deleted_group['group_name']}")
            
            # Step 5: Return optimized summary
            return {
                'success': True,
                'deleted_group': deleted_group,
                'deleted_mappings_count': len(deleted_mappings),
                'deleted_mappings': [dict(m._mapping) for m in deleted_mappings],
                'operation_summary': {
                    'group_name': deleted_group['group_name'],
                    'group_id': validated_group_id,
                    'mappings_deleted': len(deleted_mappings),
                    'force_used': force_delete,
                    'had_active_mappings': len(active_mappings) > 0
                },
                'message': f"Successfully deleted group '{deleted_group['group_name']}' and {len(deleted_mappings)} associated mappings"
            }
            
    except (UserGroupValidationError, UserGroupNotFoundError, UserGroupDeleteError, UserGroupMapperError) as e:
        # Re-raise known exceptions with context
        logger.error(f"User group deletion failed: {e}")
        raise
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during group deletion: {e}")
        raise UserGroupDeleteError(
            f"Unexpected error deleting group {group_id}: {e}"
        ) from e


def get_user_group_summary(group_id: Any) -> Dict[str, Any]:
    """Get an optimized summary of a user group and its mappings.
    
    Args:
        group_id: The ID of the group to summarize
        
    Returns:
        Dict[str, Any]: Comprehensive group summary with performance metrics
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupNotFoundError: If group doesn't exist
    """
    try:
        # Get group and mappings in a single optimized operation
        group_record, mappings = get_group_with_mappings(group_id)
        
        # Optimized mapping analysis with single pass
        active_mappings = []
        inactive_mappings = []
        
        for mapping in mappings:
            if mapping.get('is_active', True):
                active_mappings.append(mapping)
            else:
                inactive_mappings.append(mapping)
        
        # Return comprehensive summary with performance data
        return {
            'group': group_record,
            'mapping_summary': {
                'total_mappings': len(mappings),
                'active_mappings': len(active_mappings),
                'inactive_mappings': len(inactive_mappings),
                'can_delete_safely': len(active_mappings) == 0
            },
            'deletion_info': {
                'requires_force_delete': len(active_mappings) > 0,
                'estimated_operations': 1 + len(mappings),  # 1 group + N mappings
                'affected_users': len({m.get('user_id') for m in mappings if m.get('user_id')})
            },
            'mappings': mappings
        }
        
    except (UserGroupValidationError, UserGroupNotFoundError) as e:
        logger.error(f"Failed to get group summary: {e}")
        raise


# Optimized convenience functions with reduced database calls
def delete_user_group_safe(group_id: Any) -> Dict[str, Any]:
    """Safely delete a user group (optimized - will not delete if mappings exist).
    
    Args:
        group_id: The ID of the group to delete
        
    Returns:
        Dict[str, Any]: Summary of the deletion operation
        
    Raises:
        UserGroupDeleteError: If group has active mappings or deletion fails
    """
    return delete_user_group_with_mappings(group_id, force_delete=False)


def delete_user_group_force(group_id: Any) -> Dict[str, Any]:
    """Force delete a user group and all its mappings (optimized).
    
    Args:
        group_id: The ID of the group to delete
        
    Returns:
        Dict[str, Any]: Summary of the deletion operation
    """
    return delete_user_group_with_mappings(group_id, force_delete=True)


def batch_get_group_summaries(group_ids: List[Any]) -> Dict[str, Dict[str, Any]]:
    """Get summaries for multiple groups in optimized batch operation.
    
    Args:
        group_ids: List of group IDs to summarize
        
    Returns:
        Dict[str, Dict[str, Any]]: Mapping of group_id to summary data
        
    Raises:
        UserGroupValidationError: If any validation fails
    """
    results = {}
    errors = {}
    
    for group_id in group_ids:
        try:
            results[str(group_id)] = get_user_group_summary(group_id)
        except (UserGroupValidationError, UserGroupNotFoundError) as e:
            errors[str(group_id)] = str(e)
            logger.warning(f"Failed to get summary for group {group_id}: {e}")
    
    return {
        'success_count': len(results),
        'error_count': len(errors),
        'results': results,
        'errors': errors
    }


# =============================================================================
# USER GROUP MAPPER CRUD OPERATIONS
# =============================================================================

def _validate_user_id(user_id_value: Any) -> int:
    """Validate user ID parameter.
    
    Args:
        user_id_value: The user ID to validate
        
    Returns:
        int: Validated user ID
        
    Raises:
        UserGroupValidationError: If user ID is invalid
    """
    try:
        user_id = int(user_id_value)
        if user_id <= 0:
            raise UserGroupValidationError("User ID must be a positive integer")
        return user_id
    except (ValueError, TypeError) as e:
        raise UserGroupValidationError(f"User ID must be a valid integer: {e}") from e


def _validate_mapping_id(mapping_id_value: Any) -> int:
    """Validate mapping ID parameter.
    
    Args:
        mapping_id_value: The mapping ID to validate
        
    Returns:
        int: Validated mapping ID
        
    Raises:
        UserGroupValidationError: If mapping ID is invalid
    """
    try:
        mapping_id = int(mapping_id_value)
        if mapping_id <= 0:
            raise UserGroupValidationError(MAPPING_ID_POSITIVE_ERROR)
        return mapping_id
    except (ValueError, TypeError) as e:
        raise UserGroupValidationError(f"{MAPPING_ID_INTEGER_ERROR}: {e}") from e


def _validate_mapper_required_fields(mapper_data: Dict[str, Any], is_update: bool) -> None:
    """Validate required fields for mapper data.
    
    Args:
        mapper_data: Dictionary containing mapper information
        is_update: Whether this is for update operation
        
    Raises:
        UserGroupValidationError: If required fields are missing
    """
    if not mapper_data:
        raise UserGroupValidationError("Mapper data cannot be empty")
    
    if not is_update:
        required_fields = ['user_id', 'group_id']
        missing_fields = [field for field in required_fields if not mapper_data.get(field)]
        
        if missing_fields:
            raise UserGroupValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )


def _process_mapper_ids(mapper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process and validate user_id and group_id fields.
    
    Args:
        mapper_data: Raw mapper data
        
    Returns:
        Dict[str, Any]: Processed data with validated IDs
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    processed_data = {}
    
    # Validate user_id
    if 'user_id' in mapper_data:
        processed_data['user_id'] = _validate_user_id(mapper_data['user_id'])
    
    # Validate group_id using existing function
    if 'group_id' in mapper_data:
        processed_data['group_id'] = validate_group_id(mapper_data['group_id'])
    
    return processed_data


def _process_mapper_optional_fields(mapper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process optional fields for mapper data.
    
    Args:
        mapper_data: Raw mapper data
        
    Returns:
        Dict[str, Any]: Processed optional field data
    """
    processed_data = {}
    
    # Validate is_active
    if 'is_active' in mapper_data:
        processed_data['is_active'] = bool(mapper_data['is_active'])
    
    # Other optional fields
    optional_fields = ['created_by', 'updated_by', 'notes']
    for field in optional_fields:
        if field in mapper_data and mapper_data[field] is not None:
            processed_data[field] = (
                str(mapper_data[field]).strip() 
                if isinstance(mapper_data[field], str) 
                else mapper_data[field]
            )
    
    return processed_data


def _validate_mapper_data(mapper_data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """Validate user group mapper data.
    
    Args:
        mapper_data: Dictionary containing mapper information
        is_update: Whether this is for update (some fields optional)
        
    Returns:
        Dict[str, Any]: Validated mapper data
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    # Validate required fields
    _validate_mapper_required_fields(mapper_data, is_update)
    
    # Process IDs
    processed_data = _process_mapper_ids(mapper_data)
    
    # Process optional fields
    optional_data = _process_mapper_optional_fields(mapper_data)
    processed_data.update(optional_data)
    
    return processed_data


def _check_user_group_mapping_exists(db_instance: PostgresDB, user_id: int, group_id: int, 
                                    exclude_mapping_id: int = None) -> bool:
    """Check if a user-group mapping already exists.
    
    Args:
        db_instance: Database instance
        user_id: User ID
        group_id: Group ID
        exclude_mapping_id: Mapping ID to exclude from check (for updates)
        
    Returns:
        bool: True if mapping exists, False otherwise
    """
    try:
        existing_mappings = db_instance.read(
            table_name=USER_GROUP_MAPPER_TABLE,
            conditions={'user_id': user_id, 'group_id': group_id},
            limit=1
        )
        
        if existing_mappings:
            existing_id = existing_mappings[0].id
            if exclude_mapping_id is None or existing_id != exclude_mapping_id:
                return True
        
        return False
        
    except SQLAlchemyReadError as e:
        raise UserGroupMapperError(f"Failed to check mapping existence: {e}") from e


def create_user_group_mapping(mapper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user-group mapping with validation.
    
    Args:
        mapper_data: Dictionary containing mapping information
                    Required fields: user_id, group_id
                    Optional fields: is_active, created_by, notes
    
    Returns:
        Dict[str, Any]: Created mapping record with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupMapperError: If creation fails
    """
    # Validate data using Pydantic
    validated_data = validate_mapping_create_data(mapper_data)
    
    try:
        with get_db_connection() as db:
            # Check if group exists
            check_group_exists(db, validated_data['group_id'])
            
            # Check for duplicate mapping
            if _check_user_group_mapping_exists(db, validated_data['user_id'], validated_data['group_id']):
                raise UserGroupValidationError(
                    f"Mapping already exists between user {validated_data['user_id']} "
                    f"and group {validated_data['group_id']}"
                )
            
            # Create the mapping
            created_records = db.create(
                table_name=USER_GROUP_MAPPER_TABLE,
                data=validated_data
            )
            
            if not created_records:
                raise UserGroupMapperError("Failed to create mapping - no records returned")
            
            created_mapping = dict(created_records[0]._mapping)
            
            logger.info(f"Successfully created user-group mapping: User {created_mapping['user_id']} "
                       f"-> Group {created_mapping['group_id']} (ID: {created_mapping['id']})")
            
            return {
                'success': True,
                'mapping': created_mapping,
                'operation_summary': {
                    'mapping_id': created_mapping['id'],
                    'user_id': created_mapping['user_id'],
                    'group_id': created_mapping['group_id'],
                    'is_active': created_mapping.get('is_active', True),
                    'created_at': str(created_mapping.get('created_on'))
                },
                'message': f"Successfully created mapping between user {created_mapping['user_id']} "
                          f"and group {created_mapping['group_id']}"
            }
            
    except SQLAlchemyInsertError as e:
        raise UserGroupMapperError(f"Database error creating mapping: {e}") from e
    except (UserGroupValidationError, UserGroupMapperError, UserGroupNotFoundError):
        raise
    except Exception as e:
        raise UserGroupMapperError(f"Unexpected error creating mapping: {e}") from e


def read_user_group_mapping(mapping_id: Any) -> Dict[str, Any]:
    """Read a single user-group mapping by ID.
    
    Args:
        mapping_id: The ID of the mapping to read
        
    Returns:
        Dict[str, Any]: Mapping record with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupMapperError: If mapping doesn't exist
    """
    # Validate mapping ID
    validated_mapping_id = _validate_mapping_id(mapping_id)
    
    try:
        with get_db_connection() as db:
            mapping_records = db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={'id': validated_mapping_id},
                limit=1
            )
            
            if not mapping_records:
                raise UserGroupMapperError(f"User-group mapping with ID {validated_mapping_id} not found")
            
            mapping_record = dict(mapping_records[0]._mapping)
            
            # Get related group information
            try:
                group_record = check_group_exists(db, mapping_record['group_id'])
                group_info = {
                    'group_name': group_record['group_name'],
                    'group_description': group_record.get('description'),
                    'group_is_active': group_record.get('is_active')
                }
            except UserGroupNotFoundError:
                group_info = {'group_name': 'Unknown', 'group_description': None, 'group_is_active': None}
            
            return {
                'success': True,
                'mapping': mapping_record,
                'group_info': group_info,
                'metadata': {
                    'is_active': mapping_record.get('is_active', True),
                    'created_at': str(mapping_record.get('created_on')),
                    'updated_at': str(mapping_record.get('updated_on')),
                    'has_notes': bool(mapping_record.get('notes'))
                }
            }
            
    except SQLAlchemyReadError as e:
        raise UserGroupMapperError(f"Database error reading mapping: {e}") from e
    except (UserGroupValidationError, UserGroupMapperError):
        raise
    except Exception as e:
        raise UserGroupMapperError(f"Unexpected error reading mapping: {e}") from e


def read_user_group_mappings(filters: Dict[str, Any] = None, limit: int = None, 
                           offset: int = 0) -> Dict[str, Any]:
    """Read multiple user-group mappings with optional filtering and pagination.
    
    Args:
        filters: Optional filters (e.g., {'user_id': 123, 'is_active': True})
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        Dict[str, Any]: List of mapping records with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    try:
        with get_db_connection() as db:
            # Apply filters if provided
            conditions = filters if filters else {}
            
            # Validate limit and offset
            if limit is not None and limit <= 0:
                raise UserGroupValidationError("Limit must be a positive integer")
            
            if offset < 0:
                raise UserGroupValidationError("Offset must be non-negative")
            
            # Read mappings with pagination
            mappings = db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions=conditions,
                limit=limit,
                offset=offset
            )
            
            # Convert to list of dictionaries
            mapping_records = [dict(mapping._mapping) for mapping in mappings]
            
            # Get total count for pagination metadata
            total_count = len(db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions=conditions
            ))
            
            # Enhance with group information
            enhanced_mappings = []
            for mapping in mapping_records:
                try:
                    group_record = check_group_exists(db, mapping['group_id'])
                    mapping['group_name'] = group_record['group_name']
                    mapping['group_description'] = group_record.get('description')
                except UserGroupNotFoundError:
                    mapping['group_name'] = 'Unknown'
                    mapping['group_description'] = None
                
                enhanced_mappings.append(mapping)
            
            logger.debug(f"Retrieved {len(enhanced_mappings)} user-group mappings (total: {total_count})")
            
            return {
                'success': True,
                'mappings': enhanced_mappings,
                'metadata': {
                    'total_count': total_count,
                    'returned_count': len(enhanced_mappings),
                    'limit': limit,
                    'offset': offset,
                    'has_more': limit and (offset + len(enhanced_mappings)) < total_count,
                    'active_count': len([m for m in enhanced_mappings if m.get('is_active', True)]),
                    'inactive_count': len([m for m in enhanced_mappings if not m.get('is_active', True)])
                }
            }
            
    except SQLAlchemyReadError as e:
        raise UserGroupValidationError(f"Database error reading mappings: {e}") from e
    except Exception as e:
        raise UserGroupValidationError(f"Unexpected error reading mappings: {e}") from e


def update_user_group_mapping(mapping_id: Any, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a user-group mapping with validation.
    
    Args:
        mapping_id: The ID of the mapping to update
        update_data: Dictionary containing fields to update
                    Allowed fields: is_active, updated_by, notes
    
    Returns:
        Dict[str, Any]: Updated mapping record with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupMapperError: If mapping doesn't exist or update fails
    """
    # Validate using Pydantic
    validated_mapping_id = validate_positive_integer(mapping_id, "Mapping ID")
    validated_update_data = validate_mapping_update_data(update_data)
    
    try:
        with get_db_connection() as db:
            # Check if mapping exists
            existing_mapping = db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={'id': validated_mapping_id},
                limit=1
            )
            
            if not existing_mapping:
                raise UserGroupMapperError(f"User-group mapping with ID {validated_mapping_id} not found")
            
            existing_record = dict(existing_mapping[0]._mapping)
            
            # Perform update
            updated_records = db.update(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={'id': validated_mapping_id},
                data=validated_update_data
            )
            
            if not updated_records:
                raise UserGroupMapperError(
                    f"Failed to update mapping {validated_mapping_id} - no records affected"
                )
            
            updated_mapping = dict(updated_records[0]._mapping)
            
            logger.info(f"Successfully updated user-group mapping ID {validated_mapping_id}: "
                       f"User {updated_mapping['user_id']} -> Group {updated_mapping['group_id']}")
            
            return {
                'success': True,
                'mapping': updated_mapping,
                'changes': validated_update_data,
                'operation_summary': {
                    'mapping_id': validated_mapping_id,
                    'user_id': updated_mapping['user_id'],
                    'group_id': updated_mapping['group_id'],
                    'fields_updated': list(validated_update_data.keys()),
                    'updated_at': str(updated_mapping.get('updated_on')),
                    'was_active': existing_record.get('is_active'),
                    'now_active': updated_mapping.get('is_active')
                },
                'message': f"Successfully updated mapping between user {updated_mapping['user_id']} "
                          f"and group {updated_mapping['group_id']}"
            }
            
    except SQLAlchemyUpdateError as e:
        raise UserGroupMapperError(f"Database error updating mapping: {e}") from e
    except (UserGroupValidationError, UserGroupMapperError):
        raise
    except Exception as e:
        raise UserGroupMapperError(f"Unexpected error updating mapping: {e}") from e


def delete_user_group_mapping(mapping_id: Any) -> Dict[str, Any]:
    """Delete a user-group mapping.
    
    Args:
        mapping_id: The ID of the mapping to delete
        
    Returns:
        Dict[str, Any]: Summary of the deletion operation
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupMapperError: If mapping doesn't exist or deletion fails
    """
    # Validate mapping ID
    validated_mapping_id = _validate_mapping_id(mapping_id)
    
    try:
        with get_db_connection() as db:
            # Get mapping info before deletion
            existing_mapping = db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={'id': validated_mapping_id},
                limit=1
            )
            
            if not existing_mapping:
                raise UserGroupMapperError(f"User-group mapping with ID {validated_mapping_id} not found")
            
            mapping_record = dict(existing_mapping[0]._mapping)
            
            # Get group info for better logging
            try:
                group_record = check_group_exists(db, mapping_record['group_id'])
                group_name = group_record['group_name']
            except UserGroupNotFoundError:
                group_name = f"Group {mapping_record['group_id']}"
            
            # Delete the mapping
            deleted_records = db.delete(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={'id': validated_mapping_id}
            )
            
            if not deleted_records:
                raise UserGroupMapperError(
                    f"Failed to delete mapping {validated_mapping_id} - no records affected"
                )
            
            deleted_mapping = dict(deleted_records[0]._mapping)
            
            logger.info(f"Successfully deleted user-group mapping ID {validated_mapping_id}: "
                       f"User {deleted_mapping['user_id']} -> {group_name}")
            
            return {
                'success': True,
                'deleted_mapping': deleted_mapping,
                'operation_summary': {
                    'mapping_id': validated_mapping_id,
                    'user_id': deleted_mapping['user_id'],
                    'group_id': deleted_mapping['group_id'],
                    'group_name': group_name,
                    'was_active': deleted_mapping.get('is_active', True),
                    'deleted_at': str(deleted_mapping.get('updated_on', deleted_mapping.get('created_on')))
                },
                'message': f"Successfully deleted mapping between user {deleted_mapping['user_id']} "
                          f"and {group_name}"
            }
            
    except SQLAlchemyDeleteError as e:
        raise UserGroupMapperError(f"Database error deleting mapping: {e}") from e
    except (UserGroupValidationError, UserGroupMapperError):
        raise
    except Exception as e:
        raise UserGroupMapperError(f"Unexpected error deleting mapping: {e}") from e


# =============================================================================
# ADVANCED USER GROUP MAPPER OPERATIONS
# =============================================================================

def get_user_group_mappings_by_user(user_id: Any, include_inactive: bool = False) -> Dict[str, Any]:
    """Get all group mappings for a specific user.
    
    Args:
        user_id: The user ID to get mappings for
        include_inactive: Whether to include inactive mappings
        
    Returns:
        Dict[str, Any]: User's group mappings with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    # Validate user ID
    validated_user_id = _validate_user_id(user_id)
    
    try:
        # Build filters
        filters = {'user_id': validated_user_id}
        if not include_inactive:
            filters['is_active'] = True
        
        # Get mappings
        result = read_user_group_mappings(filters=filters)
        
        # Enhance with summary data
        mappings = result['mappings']
        active_mappings = [m for m in mappings if m.get('is_active', True)]
        group_names = [m.get('group_name', 'Unknown') for m in active_mappings]
        
        return {
            'success': True,
            'user_id': validated_user_id,
            'mappings': mappings,
            'summary': {
                'total_mappings': len(mappings),
                'active_mappings': len(active_mappings),
                'inactive_mappings': len(mappings) - len(active_mappings),
                'group_names': group_names,
                'group_count': len({m['group_id'] for m in active_mappings})
            }
        }
        
    except Exception as e:
        raise UserGroupValidationError(f"Error getting user mappings: {e}") from e


def get_group_user_mappings(group_id: Any, include_inactive: bool = False) -> Dict[str, Any]:
    """Get all user mappings for a specific group.
    
    Args:
        group_id: The group ID to get mappings for
        include_inactive: Whether to include inactive mappings
        
    Returns:
        Dict[str, Any]: Group's user mappings with metadata
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupNotFoundError: If group doesn't exist
    """
    # Validate group ID
    validated_group_id = validate_group_id(group_id)
    
    try:
        with get_db_connection() as db:
            # Verify group exists
            group_record = check_group_exists(db, validated_group_id)
            
            # Build filters
            filters = {'group_id': validated_group_id}
            if not include_inactive:
                filters['is_active'] = True
            
            # Get mappings
            result = read_user_group_mappings(filters=filters)
            mappings = result['mappings']
            
            # Calculate summary
            active_mappings = [m for m in mappings if m.get('is_active', True)]
            user_ids = [m['user_id'] for m in active_mappings]
            
            return {
                'success': True,
                'group': group_record,
                'mappings': mappings,
                'summary': {
                    'total_mappings': len(mappings),
                    'active_mappings': len(active_mappings),
                    'inactive_mappings': len(mappings) - len(active_mappings),
                    'user_ids': user_ids,
                    'unique_users': len(set(user_ids))
                }
            }
            
    except (UserGroupValidationError, UserGroupNotFoundError):
        raise
    except Exception as e:
        raise UserGroupValidationError(f"Error getting group mappings: {e}") from e


def bulk_create_user_group_mappings(mappings_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create multiple user-group mappings in batch.
    
    Args:
        mappings_data: List of mapping dictionaries
                      Format: [{'user_id': 1, 'group_id': 2}, ...]
    
    Returns:
        Dict[str, Any]: Summary of bulk creation operation
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    # Validate using Pydantic
    validated_mappings = validate_bulk_mapping_create_data(mappings_data)
    
    results = []
    errors = []
    skipped = []
    
    # Process each mapping
    for i, validated_data in enumerate(validated_mappings):
        try:
            with get_db_connection() as db:
                if _check_user_group_mapping_exists(db, validated_data['user_id'], validated_data['group_id']):
                    skipped.append({
                        'index': i,
                        'user_id': validated_data['user_id'],
                        'group_id': validated_data['group_id'],
                        'reason': 'Mapping already exists'
                    })
                    continue
            
            # Create the mapping
            result = create_user_group_mapping(validated_data)
            results.append({
                'index': i,
                'success': True,
                'mapping': result['mapping'],
                'user_id': result['mapping']['user_id'],
                'group_id': result['mapping']['group_id']
            })
            
        except (UserGroupValidationError, UserGroupMapperError, UserGroupNotFoundError) as e:
            error_info = {
                'index': i,
                'success': False,
                'error': str(e),
                'user_id': validated_data.get('user_id', 'unknown'),
                'group_id': validated_data.get('group_id', 'unknown')
            }
            errors.append(error_info)
            logger.warning(f"Failed to create mapping {i}: {e}")
    
    return {
        'success': len(errors) == 0,
        'total_processed': len(mappings_data),
        'successful_creations': len(results),
        'failed_creations': len(errors),
        'skipped_duplicates': len(skipped),
        'results': results,
        'errors': errors,
        'skipped': skipped,
        'summary': {
            'success_rate': len(results) / len(mappings_data) * 100 if mappings_data else 0,
            'created_mappings': [(r['user_id'], r['group_id']) for r in results],
            'failed_mappings': [(e['user_id'], e['group_id']) for e in errors]
        }
    }


def bulk_update_user_group_mappings(mapping_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update multiple user-group mappings in batch.
    
    Args:
        mapping_updates: List of dictionaries with 'mapping_id' and update data
                        Format: [{'mapping_id': 1, 'data': {'is_active': False}}, ...]
    
    Returns:
        Dict[str, Any]: Summary of bulk update operation
        
    Raises:
        UserGroupValidationError: If validation fails
    """
    if not mapping_updates:
        raise UserGroupValidationError("Mapping updates list cannot be empty")
    
    if len(mapping_updates) > 100:
        raise UserGroupValidationError("Cannot update more than 100 mappings at once")
    
    results = []
    errors = []
    
    # Process each update
    for i, update_item in enumerate(mapping_updates):
        try:
            if 'mapping_id' not in update_item or 'data' not in update_item:
                raise UserGroupValidationError(
                    f"Item {i}: Missing 'mapping_id' or 'data' field"
                )
            
            result = update_user_group_mapping(
                mapping_id=update_item['mapping_id'],
                update_data=update_item['data']
            )
            results.append({
                'mapping_id': update_item['mapping_id'],
                'success': True,
                'result': result
            })
            
        except (UserGroupValidationError, UserGroupMapperError) as e:
            error_info = {
                'mapping_id': update_item.get('mapping_id', 'unknown'),
                'success': False,
                'error': str(e)
            }
            errors.append(error_info)
            logger.warning(f"Failed to update mapping {update_item.get('mapping_id')}: {e}")
    
    return {
        'success': len(errors) == 0,
        'total_processed': len(mapping_updates),
        'successful_updates': len(results),
        'failed_updates': len(errors),
        'results': results,
        'errors': errors,
        'summary': {
            'success_rate': len(results) / len(mapping_updates) * 100 if mapping_updates else 0,
            'mappings_updated': [r['mapping_id'] for r in results],
            'mappings_failed': [e['mapping_id'] for e in errors]
        }
    }


def deactivate_user_from_group(user_id: Any, group_id: Any) -> Dict[str, Any]:
    """Deactivate a user from a group (soft delete).
    
    Args:
        user_id: The user ID
        group_id: The group ID
        
    Returns:
        Dict[str, Any]: Summary of the deactivation operation
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupMapperError: If mapping doesn't exist
    """
    # Validate IDs
    validated_user_id = _validate_user_id(user_id)
    validated_group_id = validate_group_id(group_id)
    
    try:
        with get_db_connection() as db:
            # Find the active mapping
            mappings = db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={
                    'user_id': validated_user_id,
                    'group_id': validated_group_id,
                    'is_active': True
                },
                limit=1
            )
            
            if not mappings:
                raise UserGroupMapperError(
                    f"No active mapping found between user {validated_user_id} "
                    f"and group {validated_group_id}"
                )
            
            mapping_record = mappings[0]
            mapping_id = mapping_record.id
            
            # Deactivate the mapping
            result = update_user_group_mapping(
                mapping_id=mapping_id,
                update_data={'is_active': False}
            )
            
            return {
                'success': True,
                'deactivated_mapping': result['mapping'],
                'operation_summary': {
                    'user_id': validated_user_id,
                    'group_id': validated_group_id,
                    'mapping_id': mapping_id,
                    'action': 'deactivated'
                },
                'message': f"Successfully deactivated user {validated_user_id} from group {validated_group_id}"
            }
            
    except SQLAlchemyReadError as e:
        raise UserGroupMapperError(f"Database error finding mapping: {e}") from e
    except (UserGroupValidationError, UserGroupMapperError):
        raise
    except Exception as e:
        raise UserGroupMapperError(f"Unexpected error deactivating mapping: {e}") from e


def activate_user_in_group(user_id: Any, group_id: Any) -> Dict[str, Any]:
    """Activate a user in a group (reactivate existing mapping or create new).
    
    Args:
        user_id: The user ID
        group_id: The group ID
        
    Returns:
        Dict[str, Any]: Summary of the activation operation
        
    Raises:
        UserGroupValidationError: If validation fails
        UserGroupMapperError: If operation fails
    """
    # Validate using Pydantic
    validated_params = validate_user_group_activation(user_id, group_id)
    validated_user_id = validated_params['user_id']
    validated_group_id = validated_params['group_id']
    
    try:
        with get_db_connection() as db:
            # Check if any mapping exists (active or inactive)
            existing_mappings = db.read(
                table_name=USER_GROUP_MAPPER_TABLE,
                conditions={
                    'user_id': validated_user_id,
                    'group_id': validated_group_id
                },
                limit=1
            )
            
            if existing_mappings:
                # Reactivate existing mapping
                mapping_record = existing_mappings[0]
                mapping_id = mapping_record.id
                
                if mapping_record.is_active:
                    return {
                        'success': True,
                        'action': 'already_active',
                        'mapping': dict(mapping_record._mapping),
                        'message': f"User {validated_user_id} is already active in group {validated_group_id}"
                    }
                
                # Reactivate the mapping
                result = update_user_group_mapping(
                    mapping_id=mapping_id,
                    update_data={'is_active': True}
                )
                
                return {
                    'success': True,
                    'action': 'reactivated',
                    'mapping': result['mapping'],
                    'operation_summary': {
                        'user_id': validated_user_id,
                        'group_id': validated_group_id,
                        'mapping_id': mapping_id,
                        'action': 'reactivated'
                    },
                    'message': f"Successfully reactivated user {validated_user_id} in group {validated_group_id}"
                }
            else:
                # Create new mapping
                result = create_user_group_mapping({
                    'user_id': validated_user_id,
                    'group_id': validated_group_id,
                    'is_active': True
                })
                
                return {
                    'success': True,
                    'action': 'created',
                    'mapping': result['mapping'],
                    'operation_summary': {
                        'user_id': validated_user_id,
                        'group_id': validated_group_id,
                        'mapping_id': result['mapping']['id'],
                        'action': 'created'
                    },
                    'message': f"Successfully created new mapping for user {validated_user_id} in group {validated_group_id}"
                }
                
    except SQLAlchemyReadError as e:
        raise UserGroupMapperError(f"Database error checking mapping: {e}") from e
    except (UserGroupValidationError, UserGroupMapperError, UserGroupNotFoundError):
        raise
    except Exception as e:
        raise UserGroupMapperError(f"Unexpected error activating mapping: {e}") from e