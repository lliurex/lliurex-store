#!/usr/bin/env python3

import json

errorFile=open('../install-files/usr/share/lliurex-store/files/error.json').read()                                                                                                                
errorCodes=json.loads(errorFile)

f=open("errors.po","w")

skel='msgid "%s"\n\
msgstr ""\n\n'

f.write("\n")

for item in errorCodes:
	f.write(skel%errorCodes[item])
		
f.close()
		
	
	
	

