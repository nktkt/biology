PYTHON ?= python3
SOFFICE ?= libreoffice

.PHONY: all analysis document pdf japanese japanese-pdf verify audit-source
all: document

analysis:
	$(PYTHON) analysis/run.py
	$(PYTHON) analysis/figures.py
	$(PYTHON) scripts/check_results.py

document: analysis
	$(PYTHON) paper/build_manuscript.py

pdf: document
	"$(SOFFICE)" --headless --convert-to pdf --outdir paper paper/bimane-static-quenching.docx

japanese: analysis
	$(PYTHON) analysis/figures.py --language ja
	$(PYTHON) paper/ja/build.py

japanese-pdf: japanese
	"$(SOFFICE)" --headless --convert-to pdf --outdir paper/ja paper/ja/bimane-static-quenching.ja.docx

verify:
	$(PYTHON) scripts/check_results.py

audit-source:
	$(PYTHON) scripts/audit_source.py
