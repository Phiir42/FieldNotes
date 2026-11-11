Map definitions set aside until their sheets are repainted in the game's map
style (python tools/codex_sheet.py). The build only reads tools/defs/*.py, so
nothing here ships. To bring one back: repaint its sheet, move its file up
into tools/defs/, check its areas against the new painting, and rebuild.
