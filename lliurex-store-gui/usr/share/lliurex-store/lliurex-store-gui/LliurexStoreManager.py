import lliurexstore.storeManager
import time
import Package
import Core
import random
import copy
import gettext

class LliurexStoreManager:

	def __init__(self):
		
		self.store=lliurexstore.storeManager.StoreManager(snap=True,appimage=True,autostart=True)
		# library has its own textdomain and I am forced to change it back to lliurex-store
		gettext.textdomain('lliurex-store')		
		self.core=Core.Core.get_core()
	
	#def init
	
	def list_sections(self):
		action="list_sections"
		self.store.execute_action(action,True)
		
		while self.store.is_action_running(action):
			time.sleep(0.2)
		
		print(self.store.get_status(action))
		print(self.store.get_result(action))
		print("DONE")
		
	#def search 
	
	
	def search_package(self,search_text):
		
		action="search"
		self.store.execute_action(action,search_text)
		
		packages=[]
		
		while self.store.is_action_running("search"):
			time.sleep(0.2)
			
		ret=self.store.get_status(action)
		
		if ret["status"]==0:
			data=self.store.get_result(action)
			for item in data["search"]:
				
				p=Package.Package(item)
				packages.append(p)
		
		return packages
		
	#def search_package
	
	
	def get_info(self,pkg_id):
		
		action="info"
		
		self.store.execute_action(action,pkg_id)
		while self.store.is_action_running(action):
			time.sleep(0.2)
		ret=self.store.get_status(action)
		
		if ret["status"]==0:
			
			data=self.store.get_result(action)
			try:
				p=Package.Package(data["info"][0])
			except:
				return(Package.Package())
			
			categories=copy.deepcopy(p["categories"])
			banned=set()
			
			for item in self.core.categories_manager.categories:
				if item in categories and len(categories) > 1:
					categories.remove(item)
		
			for item in self.core.categories_manager.banned_categories:
				if item in categories and len(categories) > 1:
					categories.remove(item)			
		
			'''
			if len(categories)>0:

				random_id=int(random.random()*len(categories))
				
				random_category=categories[random_id]
				pkgs,categories=self.get_package_list_from_category(random_category,10)
				
				if len(pkgs) >=10:
					samples=10
				else:
					samples=len(pkgs)
				
				for item in random.sample(pkgs,samples):
					if item["package"]!=pkg_id:
						p["related_packages"].append(item)
					
				p.fix_info()
			
			'''
			
			return p
		
	#def get_info
	
	
	def get_random_packages_from_categories(self,pkg_id,categories):
		
		for item in self.core.categories_manager.categories:
			if item in categories and len(categories) > 1:
				categories.remove(item)
		
		for item in self.core.categories_manager.banned_categories:
			if item in categories and len(categories) > 1:
				categories.remove(item)	
		
		random_id=int(random.random()*len(categories))
		random_id=int(random.random()*len(categories))
		if categories:
			random_category=categories[random_id]
		else:
			random_category="lliurex"
		pkgs,categories=self.get_package_list_from_category(random_category)
		
		p=Package.Package({})
		p.fix_info()
				
		if len(pkgs) >=10:
			samples=10
		else:
			samples=len(pkgs)
				
		for item in random.sample(pkgs,samples):
			if item["package"]!=pkg_id:
				p["related_packages"].append(item)
					
		p.fix_info()
		
		return p
		
	#def get_random_packages_from_categories
	
	
	def get_package_list_from_category(self,category_tag=None,results=0):
		
		action="list"
		self.store.execute_action(action,[category_tag],max_results=results)
		
		while self.store.is_action_running(action):
			time.sleep(0.2)
		
		packages=[]
		categories=set()
		banned=set()
		
		if category_tag in self.core.categories_manager.categories:
			for item in self.core.categories_manager.categories[category_tag]["sections"]:
				categories.add(item)
		
		for item in self.core.categories_manager.banned_categories:
			banned.add(item)
			
		
		ret=self.store.get_status(action)
		if ret["status"]==0:
			for item in self.store.get_result(action)["list"]:
				p=Package.Package(item)
				
				for category in p["categories"]:
					if type(category)!=str:
						continue
					if category not in banned and not category.startswith("X-") and category in categories:
						categories.add(category)
				
				packages.append(p)
		
		return(packages,categories)
		
	#def get_package_list
	

	def get_installed_list(self):
		
		pkgs,categories=self.get_package_list_from_category()
		ret=[]
		
		for pkg in pkgs:
			
			if pkg["state"]=="installed":
				p=Package.Package(pkg)
				ret.append(p)
				
		return ret
				
	#def get_installed_list

	
	def install_package(self,pkg_id):
		
		action="install"
		self.store.execute_action(action,pkg_id)
		
		while self.store.is_action_running(action):
			time.sleep(0.2)
			
		ret=self.store.get_status(action)	
		if ret["status"]==0:
			return True
			
		return False
		
	#def install_package
	
	
	def uninstall_package(self,pkg_id):
		
		action="remove"
		self.store.execute_action(action,pkg_id)
		
		while self.store.is_action_running(action):
			time.sleep(0.2)
			
		ret=self.store.get_status(action)	
		if ret["status"]==0:
			return True
			
		return False
		
	#def install_package

	def load_status(self):
		return (self.store.is_action_running("load"))


#class StoreManager
