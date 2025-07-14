"""
Test that __all__ stays in sync with actual public API
"""
import sys
import os

def test_all_list_exists():
    """Test that __all__ is defined and contains expected items"""
    # Read the __init__.py file directly to check __all__
    init_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '__init__.py')
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check that __all__ is defined
    assert '__all__' in content, "__all__ should be defined in __init__.py"
    
    # Check that our expected classes are in __all__
    expected_classes = [
        '"Config"',
        '"QueryRouter"', 
        '"CLIParser"',
        '"QueryProcessor"',
        '"PromptDebugClient"'
    ]
    
    for class_name in expected_classes:
        assert class_name in content, f"{class_name} should be in __all__"

def test_corresponding_files_exist():
    """Test that files exist for each class in __all__"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    # Map of classes to their expected files
    class_to_file = {
        'Config': 'config.py',
        'QueryRouter': 'router.py',
        'CLIParser': 'cli_parser.py', 
        'QueryProcessor': 'query_processor.py',
        'PromptDebugClient': 'debug_client.py'
    }
    
    for class_name, filename in class_to_file.items():
        file_path = os.path.join(base_dir, filename)
        assert os.path.exists(file_path), f"File {filename} should exist for class {class_name}"

if __name__ == "__main__":
    test_all_list_exists()
    test_corresponding_files_exist()
    print("✅ Public API tests passed!")
