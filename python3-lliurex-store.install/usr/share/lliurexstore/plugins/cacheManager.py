#The name of the main class must match the file name in lowercase
#Init: Could accept parameters if we declare them in storeManager's threads dict
import os
import lliurexstore.plugins.debManager 
import lliurexstore.plugins.appImageManager
import lliurexstore.plugins.snapManager 
import lliurexstore.plugins.infoManager 
import lliurexstore.plugins.zmdManager 
import random
import sqlite3
import threading
import time
import psutil
from queue import Queue as pool
class cachemanager:
	def __init__(self):
		self.dbg=False
		self.progress=0
		self.plugin_actions={'cache':'*','pkginfo':'*'}
		self.cli_mode=False
		self.autostart_actions={'cache':'store=self.store'} #List with actions that storeManager must launch automatically. The parameter list refers to 'stringfieds' storeManager members !!
#		self.postaction_actions={'install':'app','remove':'app'}
		self.requires={'cache':'store=self.store'}
		self.cache_dir=os.getenv("HOME")+"/.cache/lliurex-store"
		self.cache_db=self.cache_dir+'/data/info.db'
		self.db_cursor=''
		self.db=''
		self.processed=0
		self.total=0
		self.result={}
		self.disabled=None
		self.infomanager=lliurexstore.plugins.infoManager.infomanager()
		self.debmanager=lliurexstore.plugins.debManager.debmanager()
		self.appimagemanager=lliurexstore.plugins.appImageManager.appimagemanager()
		self.snapmanager=lliurexstore.plugins.snapManager.snapmanager()
		self.flatpakmanager=lliurexstore.plugins.flatpakManager.flatpakmanager()
		self.zmdmanager=lliurexstore.plugins.zmdManager.zmdmanager()
		self.insert_count=0
		self.data_pool=pool()
		self.apps_per_cycle=5 #Apps that will be processed per cycle
		self.cycles_for_commit=1 #Processed cycles needed for a commit
		self.sleep_between_cycles=10 #Time the cache plugin will sleep between a process cycle and the next
		self.sleep_between_apps=0.1 #Time the cache plugin will sleep between process one app and the next
		self.stop=False
	#def __init__
	
	def set_debug(self,dbg=True):
		self.dbg=dbg
		#self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Cache: %s'%msg)
	#def debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,action,store=None,applist=None):
		self.progress=0
		self.store=store
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=''
		if self.disabled:
			self._set_status(9)
		else:
			self._set_db()
			if action=='cache':
				self._build_cache()
			if action=='install':
				self._update(applist,'installed')
			if action=='remove':
				self._update(applist,'available')
			if action=='pkginfo':
				dataList=[]
				for appinfo in applist:
					self._debug("Looking for %s"%appinfo['package'])
					dataList.append(self._get_info(appinfo))
				self.result['data']=list(dataList)
			self.progress=100 #When all actions are launched we must assure that progress=100. 
			self.db.close()
		return(self.result)
	#def execute_action

	def set_sleep_between_apps(self,seconds):
		self.sleep_between_apps=seconds
	#def set_sleep_between_apps

	def set_sleep_between_cycles(self,seconds):
		self.sleep_between_cycles=seconds
	#def set_sleep_between_cycles

	def set_cycles_for_commit(self,count):
		self.cycles_for_commit=count
	#def set_cycles_for_commit

	def set_apps_per_cycle(self,count):
		self.apps_per_cycle=count
	#def set_apps_per_cycle

	def _callback(self):
		self.progress=self.progress+1
	#def _callback

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status
	
	def _set_db(self):
		sw_db_exists=False
		if os.path.isfile(self.cache_db):
			sw_db_exists=True
		else:
			try:
				os.makedirs(os.path.dirname(self.cache_db))
			except Exception as e:
				#self._debug(e)
				pass
		try:
			self.db=sqlite3.connect(self.cache_db)
		except Exception as e:
			#self._debug(e)
			pass
		self.db_cursor=self.db.cursor()
		if sw_db_exists==False:
			#self._debug("Creating cache table")
			self.db_cursor.execute('''CREATE TABLE data(app TEXT PRIMARY KEY, size INTEGER, state TEXT, version TEXT)''')
		self.db_cursor.execute("SELECT count(*) FROM data")
		self.processed=self.db_cursor.fetchone()
		#self._debug("%s apps present"%self.processed)
	#def _set_db

	def _build_cache(self):
		threads=[]
		semaphore = threading.BoundedSemaphore(value=self.apps_per_cycle)
		storeapps=self.store.get_apps()
		processed=[]
		for item in range(len(storeapps)-1):
			cursor=random.randint(0,len(storeapps)-1)
			app=storeapps[cursor]
			pkgname=app.get_pkgname_default()
			while pkgname in processed and len(processed)<len(storeapps):
				#self._debug("%s already processed"%pkgname)
				cursor=random.randint(0,len(storeapps)-1)
				app=storeapps[cursor]
				pkgname=app.get_pkgname_default()
				time.sleep(self.sleep_between_apps)
			processed.append(pkgname)
			th=threading.Thread(target=self._th_get_data_for_app, args = (app,semaphore))
			threads.append(th)
			th.start()
			self.insert_count+=1
			if self.insert_count==self.apps_per_cycle:
				for thread in threads:
					try:
						thread.join()
					except:
						pass
				time.sleep(self.sleep_between_cycles)
				threads=[]
			if self.insert_count==self.cycles_for_commit*self.apps_per_cycle:
				self.insert_count=0
				self._write_info()
			time.sleep(self.sleep_between_apps)
		#self._debug("Cache finished. Processed %s apps"%str(len(storeapps)-1))
	#def _build_cache

	def _write_info(self):
		processed=[]
		while self.data_pool.qsize():
			appinfo=self.data_pool.get()
			if appinfo in processed:
				#self._debug("Duplicated %s"%appinfo['package'])
				continue
			processed.append(appinfo)
			#self._debug("Writing %s to db"%appinfo['package'])
			self.db_cursor.execute('''REPLACE into data values (?,?,?,?)''', (appinfo['package'],appinfo['size'],appinfo['state'],appinfo['version']))
			time.sleep(self.sleep_between_apps)
		self._commit_bd()
	#def _write_info

	def _commit_bd(self):
		try:
			self.db.commit()
		except Exception as e:
			#self._debug("Commit error: %s. Rollback launched\n"%e)
			self.db.rollback()
	#def _commit_bd

	def _th_get_data_for_app(self,app,semaphore):
		#self._debug("Processing %s"%app.get_pkgname_default())
		app_info=self.infomanager.execute_action('info',[app],True)['data']
		package_type=self._check_package_type(app_info[0])
		#self._debug("Type %s"%package_type)
		appinfo=None
		if package_type=='deb':
			appinfo=self.debmanager.execute_action('pkginfo',app_info)['data']
		if package_type=='appimage':
			appinfo=self.appimagemanager.execute_action('pkginfo',app_info)['data']
		if package_type=='zmd':
			appinfo=self.zmdmanager.execute_action('pkginfo',app_info)['data']
		if package_type=='snap':
			appinfo=self.snapmanager.execute_action('pkginfo',app_info)['data']
		if package_type=='flatpak':
			appinfo=self.flatpakmanager.execute_action('pkginfo',app_info)['data']
		#Disabling state
		try:
			appinfo[-1]['state']=''
			#self._debug("Storing %s"%appinfo[-1]['package'])
			self.data_pool.put(appinfo[-1])
		except Exception as e:
			#self._debug("_th_get_data_for_app: %s"%e)
			pass
	#def _th_get_data_for_app

	def _check_package_type(self,appinfo):
		#Standalone installers must have the subcategory "installer"
		#Zomandos must have the subcategory "Zomando"
		#self._debug("Checking package type for app "+appinfo['name'])
		package_type=''
		if appinfo['bundle']:
			package_type=appinfo['bundle']
			if type(package_type)==type([]):
				package_type=package_type[0]
		else:
			if "Zomando" in appinfo['categories']:
				package_type="zmd"
			if 'component' in appinfo.keys():
				if appinfo['component']!='':
					package_type='deb'
			if 'flatpak' in appinfo['name']:
				package_type='flatpak'
		#Standalone installers must have an installerUrl field loaded from a bundle type=script description
			if appinfo['installerUrl']!='':
				package_type="sh"
		return(package_type)
	#def _check_package_type

	def _get_info(self,appinfo):
		#self._debug("Searching %s"%appinfo['package'])
		self.db_cursor.execute('''SELECT * FROM data WHERE app=?''',(appinfo['package'],))
		row=self.db_cursor.fetchone()
		if row:
			#self._debug("Row: %s"%str(row))
			appinfo['size']=str(row[1])
#			appinfo['state']=row[2]
			appinfo['state']=''
			appinfo['version']=row[3]
			self._set_status(0)
		else:
			self._set_status(1)
		return(appinfo)
	#def _get_info

	def _update(self,app,state):
		return
		self.db_cursor.execute('''SELECT * FROM data WHERE app=?''',(app,))
		row=self.db_cursor.fetchone()
		if row:
			#self._debug("Updating %s with state %s"%(app,state))
			query_data=(state,app)
			self.db_cursor.execute('''UPDATE data set state=? WHERE app=?''',(query_data))
			self._commit_bd()
	#def _update

	def _stop(self,stop=True):
		a=threading.Lock()
		a.acquire()
		self.stop=stop
		a.release()
	
	def _start(self,store=None):
		a=threading.Lock()
		a.acquire()
		self.stop=False
		a.release()
