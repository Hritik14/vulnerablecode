from vulnerabilities import importers
from . import nginx
from . import default

IMPROVER_REGISTRY = [
    default.DefaultImprover,
    importers.nginx.NginxTimeTravel,
]

improver_mapping = {f"{x.__module__}.{x.__name__}": x for x in IMPROVER_REGISTRY}
