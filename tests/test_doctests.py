import doctest
import importlib
import pkgutil
import unittest

import animation


def load_tests(loader, tests, ignore):
    """Run every docstring example in the package as part of the unit tests."""
    for module in pkgutil.iter_modules(animation.__path__):
        if module.name != "__main__":
            tests.addTests(doctest.DocTestSuite(importlib.import_module(f"animation.{module.name}")))
    return tests


if __name__ == "__main__":
    unittest.main()
