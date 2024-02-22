#!/usr/bin/python3
import sys
import os
import threading
import multiprocessing
import syslog
import pkgutil
import lliurexstore.plugins as plugins
import json
import random
import time
import tempfile
import dbus
import subprocess
from queue import Queue as pool
import n4d.client as n4d
from rebost import store
######
#Ver. 1.0 of storeManager.py
# This class manages the store and the related plugins
# It's implemented as an action-drived class.
# There're four(five) main actions and each of them could execute and undeterminated number of subprocess in their respective thread
# Each of these actions returns EVER a list of dictionaries.
#####

class StoreManager():
	def __init__(self,*args,**kwargs):
		self.dbg=False
		if 'dbg' in kwargs.keys() and self.dbg==False:
			self.dbg=kwargs['dbg']
		#Disable autostart (as rebost replaces all functionality)
		self.autostart=False
		if 'autostart' in kwargs.keys():
			self.autostart=kwargs['autostart']
			self._debug("Autostart actions: %s"%self.autostart)
		self._propagate_dbg=False
		self.store=None
		home=os.getenv('HOME','')
		if home=='':
		#If not home in environment export "fake home dir"
			home=tempfile.mkdtemp()
			os.environ['HOME']=home

		self.cache=os.path.join("{}".format(home,tempfile.mkdtemp),".cache/lliurex-store")
		self.cache_data=os.path.join(self.cache,"data")
		if not os.path.isdir(self.cache_data):
			os.makedirs(self.cache_data)
		self.cache_completion="%s/bash_completion"%self.cache_data
		self.related_actions={
					'load':['load'],
					'search':['search','get_info','pkginfo'],
					'list':['list','get_info','pkginfo'],
					'info':['list','get_info','pkginfo'],
					'list_sections':['list_sections'],
					'install':['search','get_info','pkginfo','install'],
					'remove':['search','get_info','pkginfo','remove']
					}
		self.cli_mode=[]			#List that controls cli_mode for plugins
		self.load=False
		self.autostart_actions=[]	#List with actions marked as autostart by plugins
		self.postaction_actions=[]	#List with actions that will be launched after other actions
		self.required_parms={}
		self.threads={}				#Dict with the functions that must execute each action
		self.static={'info':'','search':'','install':'','remove':'','list':''} #Static methods (rebost compatibility)
		self.threads_progress={}			#"" "" "" the progress for each launched thread
		self.running_threads={}			#"" "" "" the running threads
		self.plugins_registered={}		#Dict with the relation between plugins and actions 
		self.register_action_progress={}		#Dict with the progress for each function/parent_action pair
		self.action_progress={}			#Progress of global actions based on average progress of individual processes
		self.extra_actions={}		#Dict with the actions managed by plugins and no defined on the main class as related_actions
		self.result={}				#Result of the actions
		self.lock=threading.Lock()		#locker for functions related to threads (get_progress, is_action_running...)
		self.n4d=n4d.Client()
		#Disable main method as rebost replaces all functionality
		#self.main(**kwargs)
	#def __init__

	def main(self,**kwargs):
		self._define_functions_for_threads()	#Function that loads the dictionary self.threads
		self.__init_plugins__(**kwargs)			#Function that loads the plugins
		self.execute_action('load')		#Initial load of the store
		th=threading.Thread(target=self._autostart_actions)
		th.start()
	#def main

	def _autostart_actions(self):
		if self.autostart:
			for autostart_action in self.autostart_actions:
				self._debug("Autostart %s"%(autostart_action))
				self.execute_action(autostart_action)

	def _stop_autostart_actions(self):
		if self.autostart:
			for actions in self.autostart_actions:
				for action in actions.keys(): 
					if action in self.running_threads.keys():
						function=self.register_action_progress[action][0]
						function._stop()

	def _resume_autostart_actions(self):
		if self.autostart:
			for actions in self.autostart_actions:
				for action in actions.keys(): 
					if action in self.running_threads.keys():
						function=self.register_action_progress[action][0]
						function._start()
	####
	#Load and register the plugins from plugin dir
	####
	def __init_plugins__(self,**kwargs):
		package=plugins
		for importer, mod, ispkg in pkgutil.walk_packages(path=package.__path__, prefix=package.__name__+'.',onerror=lambda x: None):
			import_mod='from %s import *'%mod
			try:
				self._debug("Importing %s"%mod)
				exec (import_mod)
			except Exception as e:
				print("Import failed for %s"%mod)
				print("Reason: %s"%e)
		modules=sys.modules.copy()
		for mod in (modules.keys()):
			if 'plugins.' in mod:
				class_actions={}
				plugin_name_up=mod.split('.')[-1]
				plugin_name=plugin_name_up.lower()
				self._debug("Initializing %s"%plugin_name)
				sw_cli_mode=False
				try:
					target_class=eval(plugin_name)()
					class_actions=target_class.register()
					if 'disabled' in target_class.__dict__.keys():
						if target_class.disabled==True:
							self._debug("Disabling plugin %s"%plugin_name)
							continue
						if target_class.disabled==None:
							self._debug("Plugin %s will set its status"%plugin_name)
							pass
						else:
							#Time to check if plugin is disabled or enabled by parm
							#Values for the plugins_registered dict must be the same as the parm name that enables the plugin
							for class_action,class_plugin_name in class_actions.items():
								class_plugin=class_plugin_name
								break
							if class_plugin in kwargs.keys():
								if kwargs[class_plugin]==True:
									if target_class.disabled:
										self._debug("Disabling plugin %s"%plugin_name)
										continue
								else:
									self._debug("Disabling plugin %s"%plugin_name)
									continue
							else:
								self._debug("Disabling plugin %s"%plugin_name)
								continue
					if 'cli_mode' in target_class.__dict__.keys():
						if 'cli' in kwargs.keys():
							sw_cli_mode=True
							self._debug("Enabling cli mode for %s"%plugin_name)
					if 'autostart_actions' in target_class.__dict__.keys():
						self.autostart_actions.append(target_class.__dict__['autostart_actions'])
					if 'requires' in target_class.__dict__.keys():
						self.required_parms.update(target_class.__dict__['requires'])
					if 'postaction_actions' in target_class.__dict__.keys():
						self.postaction_actions.append({target_class:target_class.__dict__['postaction_actions']})
				except Exception as e:
					print ("Can't initialize %s %s"%(mod,target_class))
					print ("Reason: %s"%e)
			
				for action in class_actions.keys():
					if action not in self.plugins_registered:
						self.plugins_registered[action]={}
					full_module_name='plugins.'+plugin_name_up+'.'+plugin_name
					self.plugins_registered[action].update({class_actions[action]:full_module_name})
					if sw_cli_mode:
						self.cli_mode.append(full_module_name)

		self._debug(str(self.plugins_registered))
	#def __init_plugins__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg==1:
			print ('DEBUG Store: %s'%msg)
	#def _debug

	def _log(self,msg=None):
		if msg:
			syslog.openlog('lliurex-store')
			syslog.syslog(msg)
			self._debug(msg)
	####
	#dict of actions/related functions for threading
	####
	def _define_functions_for_threads(self):
		self.threads['load']="threading.Thread(target=self._load_Store,daemon=True)"
		self.threads['get_info']="threading.Thread(target=self._get_App_Info,daemon=True,args=args,kwargs=kwargs)"
		self.threads['pkginfo']="threading.Thread(target=self._get_Extended_App_Info,daemon=True,args=args,kwargs=kwargs)"
		self.threads['search']='threading.Thread(target=self._search_Store,daemon=True,args=args,kwargs=kwargs)'
		self.threads['list']='threading.Thread(target=self._search_Store,daemon=True,args=args,kwargs=kwargs)'
#		self.threads['list']='threading.Thread(target=self._get_editors_pick,args=args,kwargs=kwargs)'
		self.threads['info']='threading.Thread(target=self._search_Store,daemon=True,args=args,kwargs=kwargs)'
		self.threads['install']='threading.Thread(target=self._install_remove_App,daemon=True,args=args,kwargs=kwargs)'
		self.threads['remove']='threading.Thread(target=self._install_remove_App,daemon=True,args=args,kwargs=kwargs)'
		self.threads['list_sections']='threading.Thread(target=self._list_sections,daemon=True,args=args,kwargs=kwargs)'
		self.static['random']='self._get_editors_pick(kwargs=kwargs)'
	#def _define_functions_for_threads

	####
	#Launch the appropiate threaded function for the desired action
	#Input: 
	#  - action to be executed
	#  - parms for the action
	#Action must be a kwarg but for retrocompatibility reasons we keep it as an arg
	####
	def execute_action(self,action,*args,**kwargs):
		autostart_action=False
		#Check for autolaunchable actions
		if type(action)==type({}):
			autostart_action=True
			aux_action=list(action.keys())[0]
			kwargs.update({"action":aux_action})
			(key,value)=action[aux_action].split('=')
			kwargs.update({key:value})
			action=aux_action
		else:
			kwargs.update({"action":action})
			if action in self.required_parms.keys():
				(key,value)=self.required_parms[action].split('=')
				kwargs.update({key:value})
		self._debug("Launching action: %s with args %s and kwargs %s"%(action,args,kwargs))
		if self.is_action_running('load'):
			self._join_action('load')
			self._debug("Total apps: %s"%str(len(self.store.get_apps())))
			self._debug("Resumed action %s"%action)
		self._stop_autostart_actions()
		sw_track_status=False
		if action not in self.threads.keys():
			#Attempt to add a new action managed by a plugin
			self._debug("Attempting to find a plugin for action %s"%action)
			if action in self.plugins_registered.keys():
				for package_type,plugin in self.plugins_registered[action].items():
					self.action_progress[action]=0
					if kwargs:
						kargs={}
						for arg_name in kwargs:
							try:
								kargs.update({arg_name:eval(kwargs[arg_name])})
							except:
								kargs.update({arg_name:kwargs[arg_name]})
						kwargs=kargs.copy()
					self.threads[action]='threading.Thread(target=self._execute_class_method(action,package_type).execute_action,daemon=True,args=[],kwargs=kwargs)'
					break
				self._debug('Plugin for %s found: %s'%(action,self.plugins_registered[action]))
				if not autostart_action:
					self.related_actions.update({action:[action]})
				sw_track_status=True
		if action in self.threads.keys():
			if self.is_action_running(action):
				#join thread if we're performing the same action
				self._debug("Waiting for current action %s to end"%action)
				self.running_threads[action].join()
			try:
				self.action_progress[action]=0
				self.result[action]={}
				self.running_threads.update({action:eval(self.threads[action])})
				self.running_threads[action].start()
				if not self.running_threads[action].is_alive():
					self._debug("Relaunching!!!!!!")
					self.running_threads.update({action:eval(self.threads[action])})
					self.running_threads[action].start()
				if sw_track_status:
					self.result[action]['status']={'status':0,'msg':''}
				else:
					self.result[action]['status']={'status':-1,'msg':''}
				self._debug("Thread %s for action %s launched"%(self.running_threads[action],action))
				self._debug("Thread count: %s"%(threading.active_count()))

			except Exception as e:
				self._debug("Can't launch thread for action: %s"%action)
				self._debug("Reason: %s"%e)
				pass
#Disabled per rebost
####	elif action in self.static.keys():
####			self.action_progress[action]=0
####			self.result[action].update({'data':eval(self.static[action])})
####			self.result[action].update({'status':{'status':0,'msg':''}})
####			self.action_progress[action]=100

		#As rebost manages all actions and store has all actions disabled we call rebost at this point
		else:
			#bus=dbus.SystemBus()
			#rebost=bus.get_object("net.lliurex.rebost","/net/lliurex/rebost")
			rebost=store.client()
			self.action_progress[action]=0
			self.result[action]={}
			pkg=args[0]
			status=0
			bundle='package'
			data=[{}]
			if "." in pkg:
				try:
					(pkg,bundle)=pkg.split(".")
				except:
					print("Unable to process {}".format(pkg))
			self._debug("Calling rebost for action {0} package {1} {2}".format(action,pkg,bundle))
			if action=='info':
				self.action_progress['search']=0
				(data,status)=self._rebost_info(rebost,pkg,bundle)
			if action=='search':
				self.action_progress['info']=0
				(data,status)=self._rebost_search(rebost,pkg,bundle)
			if action=='list':
				self.action_progress['info']=0
				if 'max_results' in kwargs:
					(data,status)=self._rebost_search_category(rebost,pkg,bundle,kwargs['max_results'])
				else:
					(data,status)=self._rebost_search_category(rebost,pkg,bundle)
			if action=='install' or action=='remove':
				self.action_progress['info']=0
				user=''
	#			if bundle=='appimage':
				user=os.environ.get('USER','')
				if bundle=='zomando':
					zmdPath=os.path.join("/usr/share/zero-center/zmds","{}.zmd".format(pkg))
					appPath=os.path.join("/usr/share/zero-center/applications","{}.app".format(pkg))
					sw=False
					if os.path.isfile(zmdPath):
						if os.path.isfile(appPath):
							with open(appPath,'r') as f:
								for line in f.readlines():
									if "pkexec" in line:
										sw=True
										break
						if sw:
							proc=subprocess.run(["pkexec",zmdPath])
						else:
							proc=subprocess.run([zmdPath])
						#ZERO CENTER knows the result
						#But if a epi has check_zomando_state=False?
						#check if exists a getStatus function in script?
						#Perhaps...
						zmdVars=self.n4d.get_variable("ZEROCENTER")
						var={}
						if isinstance(zmdVars,dict):
							var=zmdVars.get(pkg,{})
						if action=='remove':
							status=0
						else:
							status=1
						if var.get('state',0)==1:
							status=-1*(status-1)
				else:
					if user=='root':
						user=''
					tmpData=rebost.testInstall(pkg,bundle,user)
					try:
						dataRebost=json.loads(tmpData)
					except Exception as e:
						print("{}".format(e))
						dataRebost=[]
					if isinstance(dataRebost,list) and len(dataRebost)>0:
						if os.path.isfile(dataRebost[0].get('epi','')):
							cmd=["pkexec","/usr/share/rebost/helper/rebost-software-manager.sh",dataRebost[0].get('epi')]
							pid=9999
							status=0
							realstatus=status
							try:
								proc=subprocess.Popen(cmd)
								proc.communicate()[0]
								pid=proc.pid
								status=proc.returncode
								realstatus=status
							except Exception as e:
								print("{}".format(e))
							if status==0:
								status=int(rebost.getEpiPkgStatus(dataRebost[0].get('script')))
								realstatus=status
								if action=="remove":
									status=-1*(status-1)
							rebost.commitInstall(pkg,bundle,"{}".format(realstatus))
						else:
							status=-1
					else:
						status=-1
					for item in dataRebost:
						item=self._rebostPkg_to_storePkg(item)
						data.append(item)
				self.action_progress['info']=100

			self.result[action].update({'data':data})
			self.result[action].update({'status':{'status':status,'msg':''}})
			self.action_progress[action]=100
			#self._debug("No function associated with action %s"%action)
			#self._debug("Rebost result for action {0}:\n{1}".format(action,data))
			#self._debug(self.result)
			self._debug(self.action_progress)
	#def execute_action

	def _rebost_info(self,rebost,pkg,bundle):
		status=0
		data=[]
		try:
			data=json.loads(rebost.showApp(pkg))
		except Exception as e:
			print("Error getting data: {}".format(e))
			data=[{}]
		if len(data):
			try:
				data=[json.loads(data[0])]
			except Exception as e:
				print("Error inspecting data: {}".format(e))
				if isinstance(data[0],dict):
					data=data[0]
				else:
					print(data)
					data=[{}]
			try:
				data[0]=self._rebostPkg_to_storePkg(data[0])
			except Exception as e:
				if isinstance(data,dict):
					data=[data]
					data[0]=self._rebostPkg_to_storePkg(data[0])
			if bundle and bundle not in data[0].get('bundle',{}.keys()):
				self._debug("Bundle not found: {}".format(bundle))
				self._debug("Bundles found: {}".format(data[0].get('bundle')))
				if len(data[0].get('bundle',{}))>0:
					bundle=list(data[0].get('bundle').keys())[0]
				else:
					for key in data[0].keys():
						data[0].update({key:''})
						status=1
			if data[0].get('bundle'):
				bundles=data[0].get('bundle')
				if 'zomando' in bundles: 
					bundle='zomando'
				if bundle=='':
					if 'package' in bundles: 
						bundle='package'
					elif 'appimage' in bundles: 
						bundle='appimage'
					elif 'snap' in bundles: 
						bundle='snap'
					elif 'flatpak' in bundles: 
						bundle='flatpak'
				data[0].update({'version':data[0]['versions'].get(bundle,'')})
				if bundle=='package':
					if data[0].get('id','').endswith(".desktop"):
						data[0]['bundle']['package']=data[0].get('id')

				data[0].update({'id':data[0]['bundle'].get(bundle,'')})
				data[0].update({'size':data[0]['size'].get(bundle,'')})
				if bundle:
					state="available"
					bundle_state=data[0].get('state',{}).get(bundle)
					if bundle_state=='0':
						state="installed"
					data[0].update({'state':"{0}".format(state)})
					if bundle!='package':
						data[0].update({'name':"{0}.{1}".format(data[0].get('name','').rstrip(),bundle)})
						data[0].update({'package':"{0}.{1}".format(data[0].get('package','').rstrip(),bundle)})
		else:
			status=1
			self.action_progress['search']=100
		return(data,status)
	#def _rebost_info
	
	def _rebost_search_category(self,rebost,category,bundle,limit=0):
		data=[]
		status=0
		dataRebost=["{}"]
		try:
			dataRebost=json.loads(rebost.getAppsInCategory(category,limit))
		except Exception as e:
			print(e)
		for rebostPkg in dataRebost:
			item=json.loads(rebostPkg)
			item=self._rebostPkg_to_storePkg(item)
			data.append(item)
		self.action_progress['info']=100
		return(data,status)
	#def _rebost_search

	def _rebost_search(self,rebost,pkg,bundle):
		data=[]
		status=0
		dataRebost=[]
		try:
			dataRebost=json.loads(rebost.searchApp(pkg))
		except Exception as e:
			print(e)
		for rebostPkg in dataRebost:
			item=json.loads(rebostPkg)
			item=self._rebostPkg_to_storePkg(item)
			data.append(item)
		self.action_progress['info']=100
		return(data,status)
	#def _rebost_search

	def _rebostPkg_to_storePkg(self,rebostPkg):
		rebostPkg.update({'package':rebostPkg.get('pkgname','').strip().rstrip()})
		rebostPkg.update({'pkgname':rebostPkg.get('package')})
		rebostPkg.update({'name':rebostPkg.get('package')})
		rebostPkg.update({'component':rebostPkg.get('package')})
		rebostPkg.update({'summary':rebostPkg.get('summary','').strip().rstrip()})
		thumbnails=rebostPkg.get('thumbnails',[])
		if thumbnails==None:
			thumbnails=[]
		screenshots=rebostPkg.get('screenshots',[])
		if screenshots==None:
			screenshots=[]
		rebostPkg.update({'screenshots':screenshots+thumbnails})
		rebostPkg.update({'updatable':0})
		rebostPkg.update({'depends':''})
		rebostPkg.update({'banner':None})
		license=rebostPkg.get('license','')
		if isinstance(license,str)==False:
			license=''
		rebostPkg.update({'license':license.strip().rstrip()})
		return(rebostPkg)
	#def _rebostPkg_to_storePkg

	def _execute_class_method(self,action,package_type,*args,launchedby=None,**kwargs):
		exe_function=None
		if not package_type:
			package_type="*"
		if action in self.plugins_registered.keys():
			self._debug("Plugin for %s: %s"%(action,self.plugins_registered[action][package_type]))
			try:
				self._debug(self.plugins_registered[action][package_type]+"("+','.join(args)+")")
				exe_function=eval(self.plugins_registered[action][package_type]+"("+','.join(args)+")")
			except Exception as e:
				self._debug("Can't launch execute_method for class %s"%e)
				pass
			if self._propagate_dbg:
				exe_function.set_debug(self.dbg)
			if self.plugins_registered[action][package_type] in self.cli_mode:
				exe_function.cli_mode=True
			self._register_action_progress(action,exe_function,launchedby)
		else:
			self._debug("No plugin for action: %s"%action)
			pass
		if kwargs:
			self._debug("Parms: %s"%kwargs)
			pass
		return (exe_function)
	#def _execute_class_method

	###
	#Tell if a a action is running
	#Input:
	#  - action to monitorize
	#Output:
	#  - status true/false
	###
	def is_action_running(self,searched_action=None):
		status=False
		action_list=[]
		if searched_action:
			action_list.append(searched_action)
		else:
			action_list=self.related_actions.keys()

		for action in action_list:
			if action in self.static.keys():
				if self.action_progress.get(action,0)!=100:
					status=True
			if action in self.running_threads.keys():
				if self.running_threads[action].is_alive():
					status=True
					break
				elif action in self.related_actions.keys():
					for related_action in self.related_actions[action]:
						if related_action in self.running_threads.keys():
							if self.running_threads[related_action].is_alive():
								status=True
								break
					
				#When in gui Glib blocks the load thread, so relaunch it if is stopped
				if ("stopped" in "%s"%self.running_threads[action] and action=='load'):
					self.running_threads.update({action:eval(self.threads[action])})
					self.running_threads[action].start()
					status=True
					break
		return(status)
	#def is_action_running

	####
	#Joins an action till finish
	#Input:
	#  - action to join
	####
	def _join_action(self,action):
		self._debug("Joining action: %s"%action)
		try:
			self.running_threads[action].join()
		except Exception as e:
			self._debug("Unable to join thread for: %s"%action)
			self._debug("Reason: %s"%e)
			pass
		finally:		
			if action in self.running_threads.keys():
				del(self.running_threads[action])
	#def _join_action

	####
	#Register the method and action/parent_action pair in the progress dict
	#Input:
	#  - action launched
	#  - function (a reference to the function)
	#  - parent_action that owns the action (if any)
	####
	def _register_action_progress(self,action,function,parent_action=None):
		if action in self.register_action_progress.keys():
			self._debug("Appended process for action: %s and function: %s"%(action,function))
			self.register_action_progress[action].append(function)
		else:
			self._debug("Registered process for action: %s and function %s"%(action,function))
			self.register_action_progress[action]=[function]
		if parent_action:
			self._debug("Registered process for Parent Action: %s-%s and function: %s"%(action,parent_action,function))
			if parent_action in self.threads_progress.keys():
				self.threads_progress[parent_action].update({action:function})
			else:
				self.threads_progress[parent_action]={action:function}
	#def _register_action_progress

	####
	#Get the progress of the executed actions
	#Input
	#  - action or none if we want all of the progress
	#Output:
	#  - Dict of results indexed by actions
	####
	def get_progress(self,action=None):
		#self._debug("Get progress for {0}".format(action))
		progress={'search':0,'list':0,'install':0,'remove':0,'load':0,'list_sections':0}
		action_list=[]
		if action in self.static.keys():
			self._debug("Rebost skips action {}".format(action))
			pass
		else:
			if action in self.register_action_progress.keys():
				action_list=[action]
			else:
				action_list=self.register_action_progress.keys()
			self.lock.acquire() #prevent that any thread attempts to change the iterator
			for parent_action in self.related_actions.keys():
				if self.is_action_running(parent_action):
					for action in action_list:
						if parent_action in self.threads_progress.keys():
							acum_progress=0
							for threadfunction,function in self.threads_progress[parent_action].items():
								acum_progress=acum_progress+function.progress
		
							count=len(self.related_actions[parent_action])
							self.action_progress[parent_action]=round(acum_progress/count,0)
							progress[parent_action]=self.action_progress[parent_action]
				else:
					if action in self.static.keys():
						self._debug("Rebost skips action {}".format(action))
						pass
					#put a 100% just in case
					if parent_action in self.action_progress.keys():
						self.action_progress[parent_action]=100
			self.lock.release()
		return(self.action_progress)
	#def get_progress

	####
	#Gets the result of an action
	#Input:
	#  - action
	#Output:
	#  - Dict of results indexed by actions
	####
	def get_result(self,action=None):
		self.lock.acquire() #Prevent changes on results from threads
		result={}
		if action==None:
			for res in self.result.keys():
				if res!='load':
					if 'data' in self.result[res]:
						result[res]=self.result[res]['data']
					else:
						result[res]=[]
		else:
			self._debug("Checking result for action %s"%action)
			if self.is_action_running(action):
				self._join_action(action)
			result[action]=[]
			if action in self.result:
				if 'data' in self.result[action]:
					result[action]=self.result[action]['data']
					if len(self.result[action]['data'])<1:
						self._debug("ERROR NO DATA")
						result[action]=[""]
				else:
					result[action]=[""]
		self.lock.release()
		if action in self.extra_actions.keys():
			self._load_Store()
		#If there's no more threads relaunch autostart_actions
		if not self.running_threads:
			self._resume_autostart_actions()
		else:
			launch=True
			for key,item in self.running_threads.items():
				if item.is_alive():
					launch=False
					break
			if launch:
				self._resume_autostart_actions()

		return(result)
	#def get_result

	####
	#Gets the status of an action
	#Input.
	# - action
	#Output:
	# - Status dict of the action
	####
	def get_status(self,action=None):
		self.lock.acquire()
		self._debug("Checking status for action %s"%action)
		result={}
		if action in self.result:
			result=self.result[action]['status']
			try:
				err_file=open('/usr/share/lliurex-store/files/error.json').read()
				err_codes=json.loads(err_file)
				err_code=str(result['status'])
				if err_code in err_codes:
					result['msg']=err_codes[err_code]
				else:
					result['msg']=u"Unknown error"
			except:
					result['msg']=u"Unknown error"
		self.lock.release()
#		print("RESULT %s: %s"%(action,result))
		return(result)
	#def get_status

	####
	#Loads the store
	####
	def _load_Store(self):
		action='load'
		#Load appstream metada first
		package_type='*'
		load_function=self._execute_class_method(action,package_type,launchedby=None)
		self.store=load_function.execute_action(action=action,store=self.store)['data']
		#Once appstream is loaded load the appstream plugins for other package types (snap, appimage...)
		store_pool=pool()
		threads=[]
		for package_type in self.plugins_registered[action]:
			if package_type!='*':
				th=threading.Thread(target=self._th_load_store, args = (store_pool,action,package_type))
				threads.append(th)
				th.start()
		for thread in threads:
			try:
				thread.join()
			except Exception as e:
				pass
		while store_pool.qsize():
			self.store=store_pool.get()
		with open(self.cache_completion,'w') as f:
			for app in self.store.get_apps():
				f.write("%s\n"%app.get_pkgname_default())
	#def _load_Store

	def _th_load_store(self,store_pool,action,package_type):
		load_function=self._execute_class_method(action,package_type,launchedby=None)
		store_pool.put(load_function.execute_action(action=action,store=self.store)['data'])

	####
	#Return a random array of applications
	#Input:
	#  - exclude_sections=[] -> Array of sections that will not be included
	#  - include_sections=[] -> Array of sections that will be included
	#  - max_results -> Max number of apps to include
	#Output:
	#  - Dict with the related info
	####
	def _get_editors_pick(self,*args,**kwargs):
		
		def load_applist():
			attempts=0
			sw_include=True
			tmp_app=random.choice(tmp_applist)
			while tmp_app in applist or tmp_app.get_state()==1:
				tmp_app=random.choice(tmp_applist)
				attempts+=1
				if attempts==9:
					tmp_app=None
					break
			if tmp_app:
				if exclude_sections or include_sections:
					tmp_app_sec=tmp_app.get_categories()
					for sec in exclude_sections:
						sw_include=True
						if sec in tmp_app_sec:
							sw_include=False
							break
					for sec in include_sections:
						sw_include=False
						if sec in tmp_app_sec:
							sw_include=True
							break

				if sw_include:
					while tmp_app in applist or tmp_app.get_state()==1:
						tmp_app=random.choice(tmp_applist)
						attempts+=1
						if attempts==9:
							tmp_app=None
							break
				else:
					tmp_app=None
			return(tmp_app)

		def select_applist():
			start_point=random.randint(0,total_apps)
			end_point=start_point+10
			if end_point>total_apps:
				diff=end_point-total_apps
				end_point=total_apps
				start_point-=diff
			tmp_applist=apps_in_store[start_point:end_point]
			return(tmp_applist)
		exclude_sections=[]
		include_sections=[]
		max_results=10
		kargs=kwargs['kwargs'].copy()
		if 'exclude_sections' in kargs.keys():
			exclude_sections=kargs['exclude_sections'].split(',')
			self._debug("Exclude sections %s"%exclude_sections)
		if 'include_sections' in kargs.keys():
			include_sections=kargs['include_sections'].split(',')
			self._debug("Only sections %s"%include_sections)
		if 'max_results' in kargs.keys():
			if kargs['max_results']:
				max_results=kargs['max_results']
		applist=[]
		apps_in_store=self.store.get_apps()
		cont=0
		total_apps=len(apps_in_store)-1
		tmp_applist=select_applist()
		while cont<max_results:
			tmp_app=load_applist()
			attempts=0
			while tmp_app==None:
				tmp_applist=select_applist()
				tmp_app=load_applist()
				attempts+=1
				if attempts>max_results*10:
					break
			if tmp_app:
				applist.append(tmp_app)
			cont+=1
		#Now transform applist into an app_info list
		appinfo=self._get_App_Info(applist)
		return(appinfo)

	####
	#Loads the info related to one app
	#Input:
	#  - List of App objects
	#Output:
	#  - Dict with the related info
	####
	def _get_App_Info(self,applist,launchedby=None):
		action='get_info'
		info_function=self._execute_class_method(action,None,launchedby=launchedby)
		info_applist=info_function.execute_action(action,applist)
		self._debug("Info collected")
		return(info_applist)
	#def _get_App_Info

	####
	#Loads the extended info related to one app (slower)
	#Input:
	#  - Dict off Apps (as returned by _get_app_info)
	#Output:
	#  - Dict with the related info
	####
	def _get_Extended_App_Info(self,info_applist,launchedby=None,fullsearch=True,channel=''):
		#Check if there's any plugin for the distinct type of packages
		action='pkginfo'
		types_dict={}
		result={}
		result['data']=[]
		result['status']={'status':0,'msg':''}
		processed=[]
		for app_info in info_applist:
			info_function=self._execute_class_method(action,'*',launchedby=launchedby)
			info_result=info_function.execute_action(action,applist=[app_info])
			self._debug(info_result)
			if info_result['status']['status']==0 and info_result['data'][0]['state']:
				result['data'].extend(info_result['data'])
			elif info_result['status']['status']==0:
				app_info=info_result['data'][0]
			#Get channel
			available_channels=self._check_package_type(app_info)
			for package_type in available_channels:
				if app_info['component']!='':
					if app_info['id'] in processed:
						self._debug("App %s processed"%app_info['id'])
						continue

				if package_type in types_dict:
					types_dict[package_type].append(app_info)
				else:
					types_dict[package_type]=[app_info]
				processed.append(app_info['id'])
		for package_type in types_dict:
			self._debug("Checking plugin for %s %s"%(action,package_type))
			if package_type in self.plugins_registered[action]:
				#Only seach full info if it's required
				if (fullsearch==False and package_type=='deb'):
					result['data'].extend(types_dict[package_type])
					continue
				self._debug("Retrieving info for %s"%types_dict[package_type])
				info_function=self._execute_class_method(action,package_type,launchedby=launchedby)
				result['data'].extend(info_function.execute_action(action,types_dict[package_type])['data'])
			else:
				result['data'].append(app_info)
		return(result)
	#def _get_Extended_App_Info

	def _list_sections(self,searchItem='',action='list_sections',launchedby=None):
		result={}
		self._debug("Retrieving all sections")
		data={}
		status={}
		if action in self.plugins_registered.keys():
			self._debug("Plugin for generic search: %s"%self.plugins_registered[action]['*'])
			finder=self.plugins_registered[action][('*')]
			search_function=eval(finder+"()")
			result=search_function.execute_action(self.store,action,searchItem)
			status=result['status']
			data=result['data']
		else:
			print("No plugin for action %s"%action)
		self.result[action]['data']=data
		self.result[action]['status']=status
		self._debug("Sections: %s"%self.result[action]['data'])
		self._debug("Status: %s"%self.result[action]['status'])

	####
	#Search the store
	#Input:
	#  - string search
	#Output:
	#  - List of dicts with all the info
	####
	def _search_Store(self,*args,**kwargs):
		search_item=args[0]
		return_msg=False
		action='search'
		if 'action' in kwargs.keys():
			action=kwargs['action']
		launchedby=None
		if 'launchedby' in kwargs.keys():
			launchedby=kwargs['launchedby']
		max_results=0
		if 'max_results' in kwargs.keys():
			max_results=kwargs['max_results'] 
		fullsearch=False
		if 'fullsearch' in kwargs.keys():
			fullsearch=kwargs['fullsearch']
		result={}
		tmp_applist=[]
		if action=='list_sections':
			search_item=''
		elif action=='info':
			fullsearch=True
		if not launchedby:
			launchedby=action
		#Set the exact match to false for search method
		exact_match=True
		if (launchedby=='search'):
				exact_match=False
		target_channel=''
		if '=' in search_item:
			target_channel=search_item.split('=')[-1]
			search_item=search_item.split('=')[0]
		for package_type in self.plugins_registered[action]:
			self._debug("Searching package type %s"%package_type)
			search_function=self._execute_class_method(action,'*',launchedby=launchedby)
			result.update(search_function.execute_action(self.store,action,search_item,exact_match,max_results))
		tmp_applist=result['data']
		status=result['status']
		realAction=action
		if status['status']==0:
			#1.- Get appstream metadata (faster)
			subordinate_action='get_info'
			self.result[subordinate_action]={}
			result=self._get_App_Info(tmp_applist,launchedby)
			self._debug("Add result for %s"%subordinate_action)
			self.result[subordinate_action]=result
			if fullsearch:
				#2.- Get rest of metadata (slower)
				self._debug("Target channel: %s"%target_channel)
				result=self._get_Extended_App_Info(result['data'],launchedby,fullsearch,target_channel)
				if launchedby:
					realAction=launchedby
					self._debug("Assigned results of %s to %s"%(action,realAction))
				if (result['status']['status']==0) or (result['status']['status']==9):
					return_msg=True
					if fullsearch:
						result['status']['status']=0
				else:
					self._debug(result)
					return_msg=False
		else:
			return_msg=False
		self.result[launchedby]['data']=result['data']
		self.result[launchedby]['status']=result['status']
		return(return_msg)
	#def _search_Store

	####
	#Install or remove an app
	#Input:
	#  - String with the app name
	#Output:
	#  - Result of the operation
	####
	def _install_remove_App(self,*args,**kwargs):
		appName=args[0]
		if 'action' in kwargs.keys():
			action=kwargs['action']
		self._log("Attempting to %s %s"%(action,appName))
		result={}
		return_msg=False
		if (self._search_Store(appName,action='search',fullsearch=True,launchedby=action)):
			info_applist=self.result[action]['data']
			types_dict={}
			#Check if package is installed if we want to remove it or vice versa
			for app_info in info_applist:
			#Appstream doesn't get the right status in all cases so we rely on the mechanisms given by the different plugins.
				if (action=='install' and app_info['state']=='installed') or (action=='remove' and app_info['state']=='available'):
					if (action=='remove' and app_info['state']=='available'):
							self.result[action]['status']={app_info['package']:3}
							self.result[action]['status']={'status':3}
					else:
						self.result[action]['status']={app_info['package']:4}
						self.result[action]['status']={'status':4}
						pass
					return_msg=False
					types_dict={}
					break
				processed=[]
				available_channels=self._check_package_type(app_info)
				for package_type in available_channels:
					if app_info['component']!='':
						if app_info['id'] in processed:
							self._debug("App %s processed"%app_info['id'])
							continue

					if package_type in types_dict:
						types_dict[package_type].append(app_info)
					else:
						types_dict[package_type]=[app_info]
					processed.append(app_info['id'])

			for package_type in types_dict:
				self._debug("Checking plugin for %s %s"%(action,package_type))
				if package_type in self.plugins_registered[action]:
					install_function=self._execute_class_method(action,package_type,launchedby=action)
					if package_type=='zmd':
					#If it's a zmd the zomando must be present in the system
						zmd_info=[]
						for zmd_bundle in types_dict[package_type]:
							zmdInfo={}
							self._debug("Cheking presence of zmd %s"%zmd_bundle['package'])
							zmd='/usr/share/zero-center/zmds/'+app_info['package']+'.zmd'
							if not os.path.exists(zmd):
								zmdInfo['package']=zmd_bundle['package']
								zmd_info.append(zmdInfo)
						if zmd_info:
							self._debug("Installing needed packages")
							install_depends_function=self._execute_class_method(action,"deb",launchedby=action)
							result=install_depends_function.execute_action(action,zmd_info)
							
					result=install_function.execute_action(action,types_dict[package_type])
					self.result[action]=result
					#Deprecated. Earlier versions stored the "app" object so here the app could get marked as installed/removed without neeed of import or query anything
					#Python>=3.6 don't let us to store the app object in a queue (needed for the GUI) so this code becames deprecated.
#					if result['status']['status']==0:
						#Mark the apps as installed or available
#						for app in types_dict[package_type]:
#							if action=='install':
#								app['appstream_id'].set_state(1)
#								self._debug("App state changed to installed")
#							else:
#								app['appstream_id'].set_state(2)
#								self._debug("App state changed to available")
					for app in types_dict[package_type]:
						self._execute_postactions(action,app['package'])
					return_msg=True
		self._log("Result %s: %s"%(action,self.result[action]))
		return(return_msg)
	#def install_App
	
	####
	#Check the package type
	#Input:
	# - AppInfo dict (element of the list returned by _get_app_info)
	#Output:
	# - String with the type (deb, sh, zmd...)
	####
	def _check_package_type(self,app_info):
		#Standalone installers must have the subcategory "installer"
		#Zomandos must have the subcategory "Zomando"
		self._debug("Checking package type for app "+app_info['name'])
		return_msg=[]
		if app_info['bundle']:
			return_msg.extend(app_info['bundle'])
		else:
			if "Zomando" in app_info['categories']:
				return_msg.append("zmd")
			if 'component' in app_info.keys():
				if app_info['component']!='':
					return_msg.append('deb')
		#Standalone installers must have an installerUrl field loaded from a bundle type=script description
			if app_info['installerUrl']!='':
				return_msg.append("sh")
		return(return_msg)
	#def _check_package_type

	def _execute_postactions(self,action,app):
		for postaction in self.postaction_actions:
			for plugin,actions in postaction.items():
				for key,val in actions.items():
					if action==key:
						self._debug("Application: %s"%app)
						plugin.execute_action(key,applist=app)
