import syslog
import gi
gi.require_version('PackageKitGlib', '1.0')
from gi.repository import PackageKitGlib as packagekit
import threading
import time
from queue import Queue as pool
class debmanager:
	def __init__(self):
		self.installer=''
		self.dbg=False
		self.result=[]
		self.progress=0
		self.partial_progress=0
		self.plugin_actions={'install':'deb','remove':'deb','pkginfo':'deb','policy':'deb'}
		self.result={}
		self.result['data']={}
		self.result['status']={}
		self.count=0
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Deb: %s'%msg)
	#def debug

	def register(self):
                return(self.plugin_actions)
	#def register
	
	#filter=1 -> app available
	#filter=2 -> only installed app installed
	def execute_action(self,action,applist,filters=1):
		self._debug("Executing action %s for %s"%(action,applist))
		self.progress=0
		self.installer=packagekit.Client()
		self.count=len(applist)
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=[]
		processedPkg=[]
		#1.- If the app doesn't exist cancel the action
		for app_info in applist:
			if app_info['package'] not in processedPkg:
				processedPkg.append(app_info['package'])
				if action=='remove':
					filters=2
				app=self._resolve_App(app_info['package'],filters)
				if app:
					if action=='install':
						self._install_App(app)
						self.result['data'].append({'package':app_info['package']})
					if action=='remove':
						self._remove_App(app)
						self.result['data'].append({'package':app_info['package']})
					if action=='pkginfo':
						res=self._get_info(app_info,app)
						self.result['data'].append(res)
					if action=='policy':
						self._set_status(0)
						self.result['data'].append({'id':app.get_id()})
				self.progress=self.progress+(self.partial_progress/self.count)
		self.progress=100
		return(self.result)
	#def execute_action

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status

	def _fake_callback(self,*args):
		pass
	#def _fake_callback

	def _callback(self,status,typ,data=None):
		self.partial_progress=status.props.percentage
		self.progress=self.partial_progress/self.count
	#def _callback

	def _install_App(self,app):
		self.return_msg=False
		self._debug("Installing %s"%app.get_id())
		err=0
		try:
			self.installer.install_packages(True,[app.get_id(),],None,self._callback,None)
			err=0
		except Exception as e:
			print(str(e))
			self._debug("Install error: %s"%e.code)
			err=e.code
		finally:
			self.partial_progress=100
		self._set_status(err)
		self._debug("Install result %s"%err)
		return err
	#def _install_App_from_Repo
			
	def _remove_App(self,app):
		try:
			self.installer.remove_packages(True,[app.get_id(),],True,False,None,self._callback,None)
			self._set_status(0)
		except Exception as e:
			#self._debug("Remove error: %s"%e.code)
			#self._debug("Remove error: %s"%e)
			self._set_status(e.code)
		finally:
			self.partial_progress=100
	#def _remove_App

	def _th_get_details(self,pkTask,app_info_pool,app):
		#self._debug("Getting details for %s"%app.get_id())
		results=pkTask.get_details([app.get_id(),],None,self._fake_callback,None)
		for app_detail in results.get_details_array():
			app_info_pool.put({'size':str(app_detail.get_size())})
			break
	#def _th_get_details

	def _th_get_depends(self,pkTask,app_info_pool,app):
		#self._debug("Getting dependencies for %s"%app.get_id())
		results=pkTask.get_depends(1,[app.get_id(),],False,None,self._fake_callback,None)
		dependsList=[]
		for related_app in results.get_package_array():
			dependsList.append(related_app.get_id())
		app_info_pool.put({'depends':dependsList})
	#def _th_get_depends

	def _get_info(self,app_info,app):
		app_info['version']=app.get_version()
		app_info['arch']=app.get_id().split(';')[2]
		pkTask=packagekit.Task()
		results=[]
		self._set_status(0)
		#Only get size and depends if we don't have the data
		if not app_info['size']:
			app_info_pool=pool()
			threads=[]
			th=threading.Thread(target=self._th_get_details, args = (pkTask,app_info_pool,app))
			threads.append(th)
			th.start()
			#Get depends disabled per time-costing
			#th=threading.Thread(target=self._th_get_depends, args = (pkTask,app_info_pool,app))
			#threads.append(th)
			#th.start()
			for thread in threads:
				try:
					thread.join()
				except:
					pass
			while app_info_pool.qsize():
				data=app_info_pool.get()
				app_info.update(data)
		#Get status
		try:
			info=app.get_info()
			state=info.to_string(info)
			if state!=app_info['state'] and state!='available' and app_info['state']=='installed':
				app_info['updatable']=1
			else:
				app_info['state']=state
			self._debug("State: %s"%state)
		except Exception as e:
			self._debug("State: not available (%s)"%e)
			pass
		#self._debug("INFO: %s"%app_info)
		return(app_info)
	#def _get_info

	def _resolve_App(self,app_name,filters=1):
		#self._debug("Resolving %s"%app_name)
		def _pk_resolve(filters,app_name):
			app=None
			self._debug("Filter for resolver: %s"%filters)
			result=self.installer.resolve(filters,[app_name,],None,self._fake_callback, None)
			resolvelist=result.get_package_array()
			#resolver bug: filters not work so if we want to remove an app first we must get the installed version...
			app_resolved=None
			if filters==1:
				app_resolved=resolvelist[0]
			elif filters==2:
				for app in resolvelist:
					if (str(app.get_info()).find('PK_INFO_ENUM_INSTALLED')!=-1):
						app_resolved=app
						break
			if app_resolved:
				self._debug("Application %s resolved succesfully"%app_resolved.get_name())
				app=app_resolved
			else:
				self._debug("Application %s NOT resolved"%app_resolved.get_name())
				pass
			return app

		app=None
		resolvelist=[]
		self.return_msg=False
		try:
			app=_pk_resolve(filters,app_name)
		except Exception as e:
			self._debug("Couldn't resolve %s"%app_name)
			self._debug("Reason: %s"%e)
			self._debug("2nd attempt")
			time.sleep(0.5)
			try:
				app=_pk_resolve(filters,app_name)
			except Exception as e:
				self._debug("Couldn't resolve %s"%app_name)
				self._debug("Reason: %s"%e)
				pass
		finally:
			self.partial_progress=100
		return(app)
	#def _resolve_App

