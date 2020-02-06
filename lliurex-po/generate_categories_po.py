#!/usr/bin/env python3

import json

f=open("../lliurex-store-gui/usr/share/lliurex-store/lliurex-store-gui/rsrc/sections.json")
a=json.load(f)
f.close()

f=open("categories.po","w")

skel='msgid "%s"\n\
msgstr ""\n\n'

x=set()

for item in a:
	if item not in x:
		f.write(skel%item)
		x.add(item)
	
	for section in a[item]["sections"]:
		if section not in x:
			f.write(skel%section)
			x.add(section)
		
		
f.close()
		
	
	
	

