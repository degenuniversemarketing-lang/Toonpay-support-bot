# This file makes src a Python package
import logging

# Configure package-level logger
logging.getLogger(__name__).addHandler(logging.NullHandler())
