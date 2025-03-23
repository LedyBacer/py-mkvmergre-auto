#!/bin/sh
test -f Application-Installer.dmg && rm Application-Installer.dmg
create-dmg \
  --volname "Py MKVMerge Auto" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "PyMKVMergeAuto.dmg" \
  "dist"