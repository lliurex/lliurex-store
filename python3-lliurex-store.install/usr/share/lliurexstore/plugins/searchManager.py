import locale
import gi
gi.require_version('AppStreamGlib', '1.0')
from gi.repository import AppStreamGlib as appstream

class searchmanager:
	def __init__(self):
		self.locale=locale.getlocale()[0]
		self.dbg=False
		self.store=''
		self.plugin_actions={'search':'*','list':'*','list_sections':'*','info':'*'}
		self.precision=1
		self.applist=[]
		self.progress=0
		self.result={}
		self.result['data']={}
		self.result['status']={}
	#def __init__

	def __call__(self):
		return (self.applist)
	#def __call__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		self._debug ("Debug enabled")
	#def set__debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Search: %s'%msg)
	#def _debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,appstreamStore,action,tokens,exact_match_for_search=False,max_results=0):
		self._debug("Executing action %s"%action)
		self._debug("Tokens: %s"%tokens)
		self.progress=0
		if type(tokens)==type([]):
			tokens=' '.join(tokens)
		if type(tokens) is str:
			tokens=tokens.lower()
		else:
			tokens=''
		if len(tokens.split(' '))>1:
			if action=='search':
				#self._debug("Tokenizing search items")
				tokens=appstream.utils_search_tokenize(tokens)
			else:
				tokens=tokens.split(' ')
		else:
			if len(tokens)>=1:
				tokens=[tokens]
			else:
				tokens=[]
	
		self.store=appstreamStore
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=[]
		if self.store:
			if action=='list':
				self._list_category(tokens,max_results)
			if action=='list_sections':
				self._list_sections()
			if (action=='search' or action=='info'):
				self._search_app(tokens,exact_match_for_search)
		else:
			#self._debug("Search needs a store")
			pass
		self.progress=100
		return(self.result)
	#def execute_action

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status

	def set_precision(self,precision):
		self.precision=precision
	#def set_precision

	def _search_app(self,tokens,exact_match):
		self._debug("Searching app "+str(tokens)+ " with exact_match="+str(exact_match))
		applist=[]
		app=None
		if exact_match and tokens:
			app=self._app_exists(tokens[0])
		if app:
			if type(app)==type([]):
				applist.extend(app)
			else:
				applist.append(app)
				self._debug("App direct match found: "+app.get_id())
		if not exact_match:
			applist.extend(self._get_apps_by_match(tokens,applist))
			applist.extend(self._get_app_by_pkgname(tokens,applist))
		applist=set(applist)
		if len(applist):
			self._set_status(0)
		else:
			self._set_status(1)
		self.result['data']=applist
		return(applist)
	#def _search_app

	def _list_sections(self):
		applist=[]
		categories={}
		for app in self.store.get_apps():
			for cat in app.get_categories():
				if cat not in categories.keys():
					categories[cat]=1
				else:
					categories[cat]=categories[cat]+1
		for section in categories:
			applist.append({str(section):categories[section]})
		self.result['data']=applist
		if len(applist):
			self._set_status(0)
		else:
			self._set_status(1)
		return(applist)
	#def _list_sections

	def _list_category(self,tokens=[],max_results=0):
		applist=[]
		self._debug("tokens: "+str(tokens))
		self._debug("Max results: %s"%max_results)
		if len(tokens)>=1:
			self._debug("Searching category "+str(tokens))
			categories_set=set(tokens)
			apps_in_store=self.store.get_apps()
			count_apps=len(apps_in_store)
			self.progress=0
			inc=100/count_apps
			for app in apps_in_store:
				self.progress=self.progress+inc
				if 'categories_set' in locals():
					try:
						app_categories=[cat.lower() for cat in app.get_categories()]
					except:
						pass
					app_categories_set=set(app_categories)
					if categories_set.issubset(app_categories_set):
						#self._debug("Found "+app.get_id())
						applist.append(app)
						if max_results and len(applist)==max_results:
							break
		else:
			self._debug("Loading all apps in store")
			applist=self.store.get_apps()
			categories_set=set(['snap','appimage'])
			applist_2=[]
			for app in applist:
				if 'categories_set' in locals():
					try:
						app_categories=[cat.lower() for cat in app.get_categories()]
					except:
						pass
					app_categories_set=set(app_categories)
					if not categories_set.issubset(app_categories_set):
						applist_2.append(app)
					else:
						print("Removing %s"%app.get_pkgname())
			applist=applist_2
			if max_results:
				applist=applist[0:max_results]
		#List only valid categories

		self.result['data']=applist
		if len(applist):
			self._set_status(0)
		else:
			self._set_status(1)
		return(applist)
	#def _list_category

	def _app_exists(self,app_name):
		#self._debug("Trying direct match for "+app_name)
		#id_matches defines how to search for an app
		# %s -> app_name; zero-lliurex-%s -> app_name with zero-lliurex- prefix and so on...
		id_matches=['%s','zero-lliurex-%s','%s.desktop']
		app=None
		for id_string in id_matches:
				#			app=self.store.get_app_by_id_ignore_prefix(id_string%app_name)
			app=self.store.get_apps_by_id(id_string%app_name)
			if app:
				break
		if not app:
		#2.- Try exact match by pkgname
			app=self.store.get_app_by_pkgname(app_name)
		self._debug("App found %s"%app)
		return(app)
	#def _app_exists

	def _get_apps_by_match(self,tokens,applist=[]):
		#Add items with match >= self.precision
		self._debug("Searching app by fuzzy match")
		if not applist:
			position=1
		else:
			position=len(applist)+1
		apps_in_store=self.store.get_apps()
		if apps_in_store:
			tmp_app_dict={}
			count_apps=len(apps_in_store)
			self.progress=0
			inc=100.0/count_apps
			for app in apps_in_store:
				self.progress=self.progress+inc
				if app not in self.applist:
					for token in tokens:
						score=app.search_matches(token)
						if score>=self.precision:
							if score in tmp_app_dict:
								tmp_app_dict[score].append(app)
							else:
								tmp_app_dict[score]=[app]
			fake_app=[]
			for match in sorted(tmp_app_dict.keys()):
				for app in tmp_app_dict[match]:
					if app not in applist:
						self._debug("Adding app "+app.get_id() + " with score: "+str(match))
						applist.insert(0,app)
		return(applist)
	#def _get_apps_by_match

	def _get_app_by_pkgname(self,tokens,applist=[]):
		if not applist:
			position=1
		else:
			position=len(applist)+1
		apps_in_store=self.store.get_apps()
		if apps_in_store:
			count_apps=len(apps_in_store)
			self.progress=0
			inc=100.0/count_apps
			for app in apps_in_store:
				self.progress=self.progress+inc
				if app not in self.applist:
					for token in tokens:
						if app.get_pkgname_default()==token:
							applist.insert(1,app)

		return(applist)
	#def _get_app_by_pkgname
