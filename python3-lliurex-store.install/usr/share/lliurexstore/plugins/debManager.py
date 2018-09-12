import syslog
import gi
gi.require_version('PackageKitGlib', '1.0')
from gi.repository import PackageKitGlib as packagekit
class debmanager:
	def __init__(self):
		self.installer=''
		self.dbg=False
		self.result=[]
		self.progress=0
		self.partial_progress=0
		self.plugin_actions={'install':'deb','remove':'deb','pkginfo':'deb'}
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

	def _log(self,msg=None):
		if msg:
			syslog.openlog('lliurex-store')
			syslog.syslog(msg)

	def register(self):
                return(self.plugin_actions)
	#def register
	
	#filter=1 -> app available
	#filter=2 -> only installed app installed
	def execute_action(self,action,applist,filters=1):
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
						self._log("Installing "+app_info['package'])
						self._install_App(app)
						self.result['data'].append({'package':app_info['package']})
					if action=='remove':
						self._log("Removing "+app_info['package'])
						self._remove_App(app)
						self.result['data'].append({'package':app_info['package']})
					if action=='pkginfo':
						self.result['data'].append(self._get_App_Extended_Info(app_info,app))
					if action=='policy':
						self._set_status(0)
						self.result['data'].append({'id':app.get_id()})
				self.progress=self.progress+(self.partial_progress/self.count)
		self.progress=100
		return(self.result)
	#def execute_action

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}

	def _fake_callback(self,status,typ,data=None):
		pass
	#def _fake_callback

	def _callback(self,status,typ,data=None):
		self.partial_progress=status.props.percentage
		self.progress=self.partial_progress/self.count
	#def _callback

	def _install_App(self,app):
		self.return_msg=False
		self._debug("Installing "+app.get_id())
		err=0
		try:
			self.installer.install_packages(True,[app.get_id(),],None,self._callback,None)
			err=0
		except Exception as e:
			print(str(e))
			self._debug("Install error: "+str(e.code))
			err=e.code
		finally:
			self.partial_progress=100
		self._set_status(err)
		return err
	#def _install_App_from_Repo
			
	def _remove_App(self,app):
		try:
			self.installer.remove_packages(True,[app.get_id(),],True,False,None,self._callback,None)
			self._set_status(0)
		except Exception as e:
			self._debug("Remove error: " +str(e.code))
			self._debug("Remove error: " +str(e))
			self._set_status(e.code)
		finally:
			self.partial_progress=100
	#def _remove_App

	def _get_App_Extended_Info(self,app_info,app):
		self._debug("Getting dependencies for "+app.get_id())
		pkTask=packagekit.Task()
		results=[]
		dependsList=[]
		self._set_status(0)
		try:
			results=pkTask.get_depends(1,[app.get_id(),],True,None,self._fake_callback,None)
		except Exception as e:
#			self._set_status(1)
			print (str(e))
			pass
		if (results):
			app_info['version']=app.get_version()
			app_info['arch']=app.get_id().split(';')[2]
			for related_app in results.get_package_array():
				dependsList.append(related_app.get_id())
			app_info['depends']=dependsList
			#app.get_version()
		try:
			results=pkTask.get_details([app.get_id(),],None,self._fake_callback,None)
		except Exception as e:
#			self._set_status(1)
			print ("ERROR %s"%e)
			pass
		if(results):
			for app_detail in results.get_details_array():
				app_info['size']=str(app_detail.get_size())
				break
		try:
			info=app.get_info()
			state=info.to_string(info)
			if state!=app_info['state'] and app_info['state']=='installed':
				app_info['updatable']=1
			else:
				app_info['state']=state
			self._debug("State: "+app_info['state'])
		except Exception as e:
			self._debug("State: not available")
				
		return(app_info)
	#def _get_App_Extended_Info

	def _resolve_App(self,app_name,filters=1):
		self._debug("Resolving "+app_name)
		app=None
		resolvelist=[]
		self.return_msg=False
		try:
			self._debug("Filter for resolver: "+str(filters))
			result=self.installer.resolve(filters,[app_name,],None,self._fake_callback, None)
			resolvelist=result.get_package_array()
			app_resolved=resolvelist[0]
			#resolver bug: filters not work so if we want to remove an app first we must get the installed version...
			if filters==2:
				for app in resolvelist:
					if (str(app.get_info()).find('PK_INFO_ENUM_INSTALLED')!=-1):
						app_resolved=app
			if app_resolved:
				self._debug("Application "+app_resolved.get_name()+" resolved succesfully")
				app=app_resolved
		except Exception as e:
			self._debug("Couldn't resolve "+app_name)
			self._debug("Reason: "+str(e))
		finally:
			self.partial_progress=100
		return(app)
	#def _resolve_App

