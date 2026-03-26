import sys, traceback

sys.argv = [
    "odoo", "-d", "tvbo_dev", "-i", "tvbo",
    "--stop-after-init", "--without-demo=True",
    "--db_host=postgres", "--db_user=odoo", "--db_password=odoo",
    "--log-level=warn"
]

# Monkey-patch preload_registries to print the actual exception
import odoo.service.server as srv
original_preload = srv.preload_registries

def patched_preload(dbnames):
    import odoo.modules.registry as reg
    original_new = reg.Registry.new
    def patched_new(*args, **kwargs):
        try:
            return original_new(*args, **kwargs)
        except BaseException as e:
            print("=" * 60, flush=True)
            print(f"CAUGHT IN Registry.new: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()
            print("=" * 60, flush=True)
            raise
    reg.Registry.new = patched_new
    return original_preload(dbnames)

srv.preload_registries = patched_preload

import odoo.cli
try:
    odoo.cli.main()
except SystemExit as e:
    print(f"\nSystemExit: {e.code}", flush=True)
except BaseException as e:
    print(f"\nBaseException: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
