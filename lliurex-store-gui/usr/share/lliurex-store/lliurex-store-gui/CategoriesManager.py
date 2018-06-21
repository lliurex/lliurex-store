import json
import Core


class CategoriesManager:
	
	def __init__(self):
		
		self.core=Core.Core.get_core()
	
		self.categories={}
		
		f=open(self.core.rsrc_dir+"sections.json")
		self.categories=json.load(f)
		f.close()
		
		self.banned_categories=["Qt","GNOME","GTK","KDE"]
		
	#def init
	