import logging as _logging

# Importing the `tvbo` package runs tvbo/__init__.py, which calls
# `logging.disable(logging.CRITICAL)` — a process-wide kill switch that silences
# ALL logging (Odoo's request/server logs and, under --test-enable, the test
# runner's output) the moment any API path lazily imports tvbo. Import it here,
# at addon load, and undo ONLY tvbo's change by restoring whatever disable level
# was in effect beforehand (rather than blanket-resetting to NOTSET, which would
# also lift a floor the deployment intentionally set). Importing the package
# itself is cheap; the heavy tvbo.datamodel.pydantic submodule stays lazily
# imported on first API use.
_prev_disable = _logging.root.manager.disable
import tvbo  # noqa: F401,E402
_logging.disable(_prev_disable)

from . import models  # noqa: E402
from . import controllers  # noqa: E402

from .models.ingest import post_init_hook  # noqa: F401,E402  (referenced by __manifest__)
