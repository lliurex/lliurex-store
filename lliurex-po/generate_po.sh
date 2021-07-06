#!/bin/bash

#./generate_categories_po.py
./generate_cli_errors_po.py

PYTHON_FILES="../lliurex-store-gui/usr/share/lliurex-store/lliurex-store-gui/*.py categories.po"
UI_FILES="../lliurex-store-gui/usr/share/lliurex-store/lliurex-store-gui/rsrc/lliurex-store.ui"

mkdir -p lliurex-store/

xgettext $UI_FILES $PYTHON_FILES -o lliurex-store/lliurex-store.pot

#CLI Files
mkdir -p python3-lliurex-store/
PYTHON_FILES="../lliurex-store-cli/usr/share/lliurex-store/*.py categories.po errors.po"
LIB_FILES="../python3-lliurex-store.install/usr/share/lliurexstore/plugins/*.py"
xgettext $LIB_FILES $PYTHON_FILES -o python3-lliurex-store/python3-lliurex-store.pot

