#!/usr/bin/env python3
"""
Simple test script to verify numpy.random functionality
"""

try:
    import numpy as np
    print("✓ NumPy imported successfully")
    print(f"NumPy version: {np.__version__}")
    print(f"NumPy file location: {np.__file__}")
    
    # Test if random module is available
    if hasattr(np, 'random'):
        print("✓ np.random is available")
        
        # Test basic random functionality
        try:
            random_array = np.random.rand(3, 3)
            print("✓ np.random.rand() works")
            print(f"Random array shape: {random_array.shape}")
            print(f"Random array:\n{random_array}")
            
            # Test random integers
            random_ints = np.random.randint(1, 100, size=5)
            print("✓ np.random.randint() works")
            print(f"Random integers: {random_ints}")
            
            # Test random choice
            choices = np.random.choice(['A', 'B', 'C', 'D'], size=3)
            print("✓ np.random.choice() works")
            print(f"Random choices: {choices}")
            
        except Exception as e:
            print(f"✗ Error testing np.random functions: {e}")
    else:
        print("✗ np.random is NOT available")
        print(f"Available attributes in np: {[attr for attr in dir(np) if not attr.startswith('_')][:10]}")
        
except ImportError as e:
    print(f"✗ Failed to import numpy: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

print("\n" + "="*50)
print("NumPy installation test completed") 