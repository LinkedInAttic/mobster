# http://stackoverflow.com/questions/1675734/how-do-i-create-a-namespace-package-in-python
import pkgutil

# First try and pull in pkg_resources from setuptools
try:
  __import__('pkg_resources').declare_namespace(__name__)
except ImportError:
  pass

# Then the standard lib pkgutil.
__path__ = pkgutil.extend_path(__path__, __name__)
