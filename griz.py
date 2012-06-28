import sys
from validator.validate import validate

print validate(sys.argv[1], format="json")
