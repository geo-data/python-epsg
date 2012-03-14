"""
Test utilities
"""
import os.path

def getTestFile():
    return os.path.join(os.path.dirname(__file__), 'test.xml')
