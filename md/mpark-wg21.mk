THIS_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

OUTDIR := .
DEFAULTS := $(THIS_DIR)defaults.yaml
include $(THIS_DIR)wg21/Makefile

$(THIS_DIR)defaults.yaml : $(THIS_DIR)defaults.py
	$< > $@

EXTRA_ARGS ?=

%.html : $(DEPS) $(THIS_DIR)pandoc.css
	$(PANDOC) \
	--bibliography $(DATADIR)/csl.json \
	$(EXTRA_ARGS)
