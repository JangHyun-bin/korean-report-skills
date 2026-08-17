# -*- coding: utf-8 -*-
"""기존 ``scripts/qa.py`` 경로를 유지하는 호환 진입점."""
import importlib.util
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_IMPL = _ROOT / "plugins" / "korean-report" / "skills" / "korean-report-doc" / "assets" / "qa.py"
_SPEC = importlib.util.spec_from_file_location("_korean_report_qa", _IMPL)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"QA 구현을 불러올 수 없다: {_IMPL}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

run = _MODULE.run
main = _MODULE.main


if __name__ == "__main__":
    sys.exit(main())
