"""
Example usage and testing script for User Group CRUD operations.

This script demonstrates how to use the user group management functions
with proper error handling and best practices.
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the user group management functions
try:
    from system.system.database_functions.user_group_management import user_group_management as ugm
    from system.system.database_functions.exceptions import (
        UserGroupValidationError,
        UserGroupNotFoundError,
        UserGroupCreateError,
        UserGroupUpdateError,
        UserGroupDeleteError
    )
except ImportError as e:
    logger.error(f"Failed to import user group management: {e}")
    exit(1)


def test_create_group():
    """Test creating a new user group."""
    print("\n=== Testing Group Creation ===")
    
    group_data = {
        'group_name': 'Test Admin Group',
        'description': 'A test group for administrators',
        'is_active': True,
        'created_by': 'test_user'
    }
    
    try:
        result = ugm.create_user_group(group_data)
        print(f"✅ Created group: {result['group']['group_name']} (ID: {result['group']['id']})")
        return result['group']['id']
        
    except UserGroupValidationError as e:
        print(f"❌ Validation error: {e}")
        return None
    except UserGroupCreateError as e:
        print(f"❌ Creation error: {e}")
        return None


def test_read_group(group_id: int):
    """Test reading a user group."""
    print(f"\n=== Testing Group Read (ID: {group_id}) ===")
    
    try:
        result = ugm.read_user_group(group_id)
        group = result['group']
        metadata = result['metadata']
        
        print(f"✅ Found group: {group['group_name']}")
        print(f"   Description: {group['description']}")
        print(f"   Active: {group.get('is_active', 'Unknown')}")
        print(f"   Total mappings: {metadata['total_mappings']}")
        print(f"   Active mappings: {metadata['active_mappings']}")
        
        return group
        
    except UserGroupNotFoundError as e:
        print(f"❌ Group not found: {e}")
        return None
    except UserGroupValidationError as e:
        print(f"❌ Validation error: {e}")
        return None


def test_read_multiple_groups():
    """Test reading multiple groups with pagination."""
    print("\n=== Testing Multiple Groups Read ===")
    
    try:
        # Get first 5 active groups
        result = ugm.read_user_groups(
            filters={'is_active': True},
            limit=5,
            offset=0
        )
        
        groups = result['groups']
        metadata = result['metadata']
        
        print(f"✅ Retrieved {metadata['returned_count']} of {metadata['total_count']} groups")
        print(f"   Has more: {metadata['has_more']}")
        
        for group in groups:
            print(f"   - {group['group_name']}: {group['description']}")
            
        return groups
        
    except UserGroupValidationError as e:
        print(f"❌ Validation error: {e}")
        return []


def test_update_group(group_id: int):
    """Test updating a user group."""
    print(f"\n=== Testing Group Update (ID: {group_id}) ===")
    
    update_data = {
        'description': 'Updated description for test group',
        'is_active': True,
        'updated_by': 'test_user_updater'
    }
    
    try:
        result = ugm.update_user_group(group_id, update_data)
        group = result['group']
        changes = result['changes']
        
        print(f"✅ Updated group: {group['group_name']}")
        print(f"   Changes made: {list(changes.keys())}")
        print(f"   New description: {group['description']}")
        
        return group
        
    except UserGroupNotFoundError as e:
        print(f"❌ Group not found: {e}")
        return None
    except UserGroupValidationError as e:
        print(f"❌ Validation error: {e}")
        return None
    except UserGroupUpdateError as e:
        print(f"❌ Update error: {e}")
        return None


def test_search_groups():
    """Test searching for groups."""
    print("\n=== Testing Group Search ===")
    
    search_term = 'test'
    
    try:
        result = ugm.search_user_groups(
            search_term=search_term,
            search_fields=['group_name', 'description'],
            limit=10
        )
        
        groups = result['groups']
        metadata = result['search_metadata']
        
        print(f"✅ Search for '{search_term}' found {metadata['total_matches']} matches")
        print(f"   Showing {metadata['returned_count']} results")
        
        for group in groups:
            print(f"   - {group['group_name']} (score: {group['relevance_score']})")
            
        return groups
        
    except UserGroupValidationError as e:
        print(f"❌ Search error: {e}")
        return []


def test_bulk_update():
    """Test bulk updating multiple groups."""
    print("\n=== Testing Bulk Update ===")
    
    # First, get some group IDs to update
    try:
        groups_result = ugm.read_user_groups(limit=3)
        if not groups_result['groups']:
            print("❌ No groups available for bulk update test")
            return
        
        # Prepare bulk updates
        updates = []
        for group in groups_result['groups'][:2]:  # Update first 2 groups
            updates.append({
                'group_id': group['id'],
                'data': {
                    'description': f"Bulk updated: {group['description']}",
                    'updated_by': 'bulk_test_user'
                }
            })
        
        result = ugm.bulk_update_user_groups(updates)
        
        print("✅ Bulk update completed")
        print(f"   Success rate: {result['summary']['success_rate']:.1f}%")
        print(f"   Successfully updated: {result['summary']['groups_updated']}")
        
        if result['errors']:
            print(f"   Failed updates: {result['summary']['groups_failed']}")
            
        return result
        
    except Exception as e:
        print(f"❌ Bulk update error: {e}")
        return None


def test_group_summary(group_id: int):
    """Test getting group summary."""
    print(f"\n=== Testing Group Summary (ID: {group_id}) ===")
    
    try:
        result = ugm.get_user_group_summary(group_id)
        
        group = result['group']
        mapping_summary = result['mapping_summary']
        deletion_info = result['deletion_info']
        
        print(f"✅ Group Summary: {group['group_name']}")
        print(f"   Total mappings: {mapping_summary['total_mappings']}")
        print(f"   Active mappings: {mapping_summary['active_mappings']}")
        print(f"   Can delete safely: {mapping_summary['can_delete_safely']}")
        print(f"   Requires force delete: {deletion_info['requires_force_delete']}")
        print(f"   Affected users: {deletion_info['affected_users']}")
        
        return result
        
    except UserGroupNotFoundError as e:
        print(f"❌ Group not found: {e}")
        return None
    except UserGroupValidationError as e:
        print(f"❌ Validation error: {e}")
        return None


def test_safe_delete(group_id: int):
    """Test safe deletion of a group."""
    print(f"\n=== Testing Safe Delete (ID: {group_id}) ===")
    
    try:
        # Get summary first to check if safe delete is possible
        summary = ugm.get_user_group_summary(group_id)
        group_name = summary['group']['group_name']
        
        if summary['mapping_summary']['can_delete_safely']:
            print(f"   Group '{group_name}' can be safely deleted")
            result = ugm.delete_user_group_safe(group_id)
            print(f"✅ Safely deleted group: {result['deleted_group']['group_name']}")
            print(f"   Deleted {result['deleted_mappings_count']} mappings")
            return True
        else:
            active_mappings = summary['mapping_summary']['active_mappings']
            print(f"   Group '{group_name}' has {active_mappings} active mappings")
            print("   Safe delete not possible - would need force delete")
            return False
            
    except UserGroupNotFoundError as e:
        print(f"❌ Group not found: {e}")
        return False
    except UserGroupDeleteError as e:
        print(f"❌ Delete error: {e}")
        return False


def run_comprehensive_test():
    """Run a comprehensive test of all CRUD operations."""
    print("🚀 Starting Comprehensive User Group CRUD Test")
    print("=" * 60)
    
    created_group_id = None
    
    try:
        # 1. Create a test group
        created_group_id = test_create_group()
        if not created_group_id:
            print("❌ Test failed: Could not create test group")
            return
        
        # 2. Read the created group
        group = test_read_group(created_group_id)
        if not group:
            print("❌ Test failed: Could not read created group")
            return
        
        # 3. Read multiple groups
        test_read_multiple_groups()
        
        # 4. Update the group
        updated_group = test_update_group(created_group_id)
        if not updated_group:
            print("❌ Test failed: Could not update group")
            return
        
        # 5. Search for groups
        test_search_groups()
        
        # 6. Test bulk operations
        test_bulk_update()
        
        # 7. Get group summary
        test_group_summary(created_group_id)
        
        # 8. Test safe delete
        deleted = test_safe_delete(created_group_id)
        if deleted:
            created_group_id = None  # Successfully deleted
        
        print("\n" + "=" * 60)
        print("✅ Comprehensive test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with unexpected error: {e}")
        logger.exception("Unexpected error during testing")
        
    finally:
        # Cleanup: Try to delete the test group if it still exists
        if created_group_id:
            try:
                print(f"\n🧹 Cleaning up test group (ID: {created_group_id})")
                result = ugm.delete_user_group_force(created_group_id)
                print(f"✅ Cleanup successful: Deleted {result['deleted_group']['group_name']}")
            except Exception as e:
                print(f"⚠️  Cleanup warning: Could not delete test group: {e}")


def demonstrate_error_handling():
    """Demonstrate proper error handling patterns."""
    print("\n🛡️  Demonstrating Error Handling Patterns")
    print("=" * 50)
    
    # 1. Validation errors
    print("\n--- Testing Validation Errors ---")
    try:
        ugm.create_user_group({'group_name': 'A'})  # Too short
    except UserGroupValidationError as e:
        print(f"✅ Caught validation error: {e}")
    
    try:
        ugm.create_user_group({})  # Missing required fields
    except UserGroupValidationError as e:
        print(f"✅ Caught missing fields error: {e}")
    
    # 2. Not found errors
    print("\n--- Testing Not Found Errors ---")
    try:
        ugm.read_user_group(99999)  # Non-existent ID
    except UserGroupNotFoundError as e:
        print(f"✅ Caught not found error: {e}")
    
    # 3. Invalid search parameters
    print("\n--- Testing Search Validation ---")
    try:
        ugm.search_user_groups('', limit=5)  # Empty search term
    except UserGroupValidationError as e:
        print(f"✅ Caught search validation error: {e}")
    
    try:
        ugm.search_user_groups('test', limit=2000)  # Limit too high
    except UserGroupValidationError as e:
        print(f"✅ Caught limit validation error: {e}")
    
    print("\n✅ Error handling demonstration completed!")


if __name__ == "__main__":
    # Run the comprehensive test
    run_comprehensive_test()
    
    # Demonstrate error handling
    demonstrate_error_handling()
    
    print("\n🎉 All tests completed!")
    print("\nTo run individual tests, call the test functions directly:")
    print("  - test_create_group()")
    print("  - test_read_group(group_id)")
    print("  - test_update_group(group_id)")
    print("  - test_search_groups()")
    print("  - etc.")
