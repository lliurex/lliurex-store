import random
import string
import os

import MainWindow
import MainMenu
import PopupMenu
import DetailsBox
import ScreenshotViewer
import LoadingBox
import SearchBox
import LliurexStoreManager
import ResourcesManager
import CategoriesManager


RSRC_DIR="/usr/share/lliurex-store/lliurex-store-gui/rsrc/"


class Core:
	
	singleton=None
	DEBUG=True
	
	@classmethod
	def get_core(self):
		
		if Core.singleton==None:
			Core.singleton=Core()
			Core.singleton.init()

		return Core.singleton
	
	@classmethod
	def get_random_id(self):
		
		chars=string.ascii_lowercase
		size=10
		
		return ''.join(random.choice(chars) for _ in range(size))
		
	#def get_random_id
	
	
	def __init__(self,args=None):
		
		self.id = random.random()
		self.rsrc_dir=RSRC_DIR
		self.ui_path=RSRC_DIR+"lliurex-store.ui"
		
		try:
			cache_dir=os.environ["XDG_CACHE_HOME"]
		except:
			cache_dir=os.path.expanduser("~/.cache/")
		
		self.tmp_store_dir=cache_dir+"/lliurex-store/"
		
		if not os.path.exists(self.tmp_store_dir):
			os.makedirs(self.tmp_store_dir)
		
		self.dprint("INIT...")
		
	#def __init__
	
	
	def init(self):
		
		self.dprint("Creating categories manager...")
		self.categories_manager=CategoriesManager.CategoriesManager()
		self.dprint("Creating resources manager...")
		self.resources=ResourcesManager.ResourcesManager()
		self.dprint("Creating store manager...")
		self.store=LliurexStoreManager.LliurexStoreManager()
		self.dprint("Creating loading screen...")
		self.loading_box=LoadingBox.LoadingBox()
		self.dprint("Creating main menu...")
		self.main_menu=MainMenu.MainMenu()
		self.dprint("Creating popup menu...")
		self.popup_menu=PopupMenu.PopupMenu()
		self.dprint("Creating details box...")
		self.details_box=DetailsBox.DetailsBox()
		self.dprint("Creating screenshot viewer...")
		self.screenshot_viewer=ScreenshotViewer.ScreenshotViewer()
		self.dprint("Creating search box...")
		self.search_box=SearchBox.SearchBox()
		
		
		self.dprint("Creating main window...")
		self.main_window=MainWindow.MainWindow()
		
	#def init
	
	
	def dprint(self,msg):
		
		if Core.DEBUG:
			print("[CORE] %s"%msg)
			
	#def dprint
	
	