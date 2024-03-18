"""Combine multiple tests and executes them together."""

import unittest

import test_integration, test_unit


if __name__ == "__main__":
    # Initialize
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    
    # Combine tests
    suite.addTests(loader.loadTestsFromModule(test_integration))
    suite.addTests(loader.loadTestsFromModule(test_unit))

    # Run
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
