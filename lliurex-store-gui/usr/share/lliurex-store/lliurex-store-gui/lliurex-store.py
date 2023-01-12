#! /usr/bin/python3
import sys
sys.path.append('/srv/svn/xenial/lliurex-store/trunk/fuentes/lliurex-appstore.install/usr/share/lliurex-store')
import Core

if __name__=="__main__":
	
	c=Core.Core.get_core()
	c.main_window.start_gui()
