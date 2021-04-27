#!/usr/bin/env python3
import os
import shutil
import gi
from gi.repository import Gio
gi.require_version ('Flatpak', '1.0')
from gi.repository import Flatpak
gi.require_version('AppStreamGlib', '1.0')
from gi.repository import AppStreamGlib as appstream
import json
#import rebostHelper
#Needed for async find method, perhaps only on xenial
wrap=Gio.SimpleAsyncResult()

class flatpakmanager():
	def __init__(self,*args,**kwargs):
		self.dbg=False
		self.enabled=True
		self.packagekind="flatpak"
		self.plugin_actions={'install':'flatpak','remove':'flatpak','pkginfo':'flatpak','load':'flatpak'}
		#self.autostartActions=["load"]
		self.priority=1
		self.store=None
		self.disabled=False
		self.progressQ={}
		self.progress={}
		self.resultQ={}
		self.result={}
		self.wrkDir='/tmp/.cache/rebost/xml/flatpak'
		self.cache_dir=os.getenv("HOME")+"/.cache/lliurex-store"
		self.cache_xmls=self.cache_dir+'/xmls/flatpak'
		self.cache_last_update=self.cache_xmls+'/.flatpak.lu'

	def setDebugEnabled(self,enable=True):
		self._debug("Debug %s"%enable)
		self.dbg=enable
		self._debug("Debug %s"%self.dbg)

	def _debug(self,msg):
		if self.dbg:
			print("flatpak: %s"%str(msg))

	def _on_error(self,action,e):
		self.progressQ[action].put(100)
		self.resultQ[action].put(str(json.dumps([{'name':action,'description':'Error','error':"1",'errormsg':str(e)}])))
	
	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,action,applist=None,store=None,results=0):
		if store:
			self.store=store
		else:
			self.store=appstream.Store()
		self.progress=0
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=''
		
		if self.disabled==True:
			self._set_status(9)
			self.result['data']=self.store
		else:
			self._check_dirs()
			dataList=[]
			if action=='load':
				self.result['data']=self._loadStore(self.store)
			else:
				for app_info in applist:
					self.partial_progress=0
					if action=='install':
						dataList.append(self._install(app_info))
					if action=='remove':
						dataList.append(self._remove(app_info))
					if action=='pkginfo':
						dataList.append(self._get_info(app_info))
						#dataList.append((app_info))
					self.progress+=round(self.partial_progress/len(applist),1)
					if self.progress>98:
						self.progress=98
				self.result['data']=list(dataList)
		self.progress=100
		return(self.result)
	#def execute_action
	
	def _check_dirs(self):
		if not os.path.isdir(self.cache_xmls):
			os.makedirs(self.cache_xmls)
	#def _check_dirs
	
	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status

	def _searchPackage(self,package):
		self._debug("Searching %s"%package)
		pklist=None
		package=package.replace("_","-")
		apps=appstream.Store()
		searchStore=[]
		for app in self.store.get_apps():
			if app.search_matches(package)>90:
				apps.add_app(app)
		searchResults=rebostHelper.appstream_to_rebost(apps)
		return(searchResults)

	def _get_info(self,app_info):
		flInst=Flatpak.get_system_installations()
		for installer in flInst:
			flRemote=installer.list_remotes()
			remoteInst=installer
			break
		try:
			installer.get_installed_ref(Flatpak.RefKind.APP,app_info['id'],None,'stable',None)
			app_info['state']='installed'
		except Exception as e:
			app_info['state']='available'
		self._set_status(0)
		return app_info


	def execute2(self,procId,action,progress,result,store,args=''):
		self.procId=procId
		if action in self.actions:
			self.progressQ[action]=progress
			self.resultQ[action]=result
			self.progress[action]=0
			if action=='load':
				self._loadStore()
			if action=='install':
				self._install(args)
			if action=='remove':
				self._remove(args)

	def _loadStore(self,store):
		action="load"
		store=self._get_flatpak_catalogue()
		for app in store.get_apps():
			self.store.add_app(app)
		return(self.store)

	def _get_flatpak_catalogue(self):
		action="load"
		rebostPkgList=[]
		sections=[]
		progress=0
		inc=0
		flInst=''
		store=appstream.Store()
		store2=appstream.Store()
		#metadata=appstream.Metadata()
		try:
			#Get all the remotes, copy appstream to wrkdir
			flInst=Flatpak.get_system_installations()
			for installer in flInst:
				flRemote=installer.list_remotes()
				for remote in flRemote:
					srcDir=remote.get_appstream_dir().get_path()
					installer.update_appstream_sync(remote.get_name())
			#sections=self.snap_client.get_sections_sync()
		except Exception as e:
			print(e)
			#self._on_error("load",e)

		try:
			store.from_file(Gio.File.parse_name(os.path.join(srcDir,"appstream.xml")))
		except Exception as e:
			print(e)
			pass
		added=[]
		for pkg in store.get_apps():
			idx=pkg.get_id()
			idxList=idx.split(".")
			if len(idxList)>2:
				idxList[0]="org"
				idxList[1]="flathub"
				newId=".".join(idxList).lower()
			else:
				newId="org.flathub.{}".format(idx[-1])
			#pkg.set_id(newId)
			state="available"
			for installer in flInst:
				installed=False
				try:
					installed=installer.get_installed_ref(0,pkg.get_name())
				except:
					try:
						installed=installer.get_installed_ref(1,pkg.get_name())
					except:
						pass
				if installed:
					state="installed"
					break
			add=False
			if not pkg.get_bundles():
				bundle=appstream.Bundle()
				bundle.set_id("{};amd64;{}".format(pkg.get_id(),state))
				bundle.set_kind(appstream.BundleKind.FLATPAK)
				pkg.add_bundle(bundle)
				add=True
			else:
				for bundle in pkg.get_bundles():
					bundle.set_id("{};amd64;{}".format(pkg.get_id(),state))
					bundle.set_kind(appstream.BundleKind.FLATPAK)
					add=True
			if add and pkg.get_id() not in added:
				try:
						#	if not (app.validate()):
					pkg.set_name("C",pkg.get_name().lower()+'.flatpak')
					pkg.add_pkgname(pkg.get_name())
					store2.add_app(pkg)
				#	else:
				#		pass
				#		print(app.validate())
				except:
					pass
				added.append(pkg.get_id())
			self._debug("Loading flatpak metadata")
		return(store2)

	def _processRemote(self,installer,remote):
		for remoteRef in installer.list_remote_refs_sync_full(remote.get_name(),Flatpak.QueryFlags.NONE):
			flat=installer.get_remote_by_name(remoteRef.get_name())

	def _install(self,app_info):
		#self._debug("Installing %s"%app_info['name'])
		action="install"
		flInst=Flatpak.get_system_installations()
		for installer in flInst:
			flRemote=installer.list_remotes()
			remoteInst=installer
			for remote in flRemote:
				remoteName=remote.get_name()
				break
			transaction=Flatpak.Transaction.new_for_installation(installer)
			break
#		ref=remoteInst.install(remoteName,Flatpak.RefKind.APP,app_info['id'],None,'stable',None,None,None)
#		for relRef in remoteInst.list_remote_related_refs_sync(remoteName,ref.format_ref()):
#			if relRef.should_download():
#				self._debug("Installing related ref %s"%relRef.get_name())
#				remoteInst.install(remoteName,Flatpak.RefKind.APP,relRef.format_ref(),None,'stable',None,None,None)

		if transaction:
	   	#Get remote ref
			print(remoteName)
			remoteRef=remoteInst.fetch_remote_ref_sync(remoteName,Flatpak.RefKind.APP,app_info['id'],None,'stable',None)
			print(remoteRef)
			print(app_info['id'])
			#transaction.add_install(remoteName,remoteRef.get_remote_name(),None)
			transaction.add_install(remoteName,remoteRef.format_ref(),None)
			print(transaction)
			transaction.run()
	   #self._debug("Installed %s"%app_info)
#		self.resultQ[action].put(str(json.dumps([result])))
#		self.progress[action] = 100
#		self.progressQ[action].put(int(self.progress[action]))
		app_info['state']='installed'
		self._set_status(0)
		return app_info
	#def _install_snap
		
	def _callback(self,client,change, _,user_data):
	    # Interate over tasks to determine the aggregate tasks for completion.
		action='install'
		if action not in self.progress.keys():
			action='remove'
			
		total = 0
		done = 0
		for task in change.get_tasks():
			total += task.get_progress_total()
			done += task.get_progress_done()
		acum=round((done/total)*100)
		if acum>self.progress[action]:
			self.progress[action]=acum
		if not self.progressQ[action].empty():
			while not self.progressQ[action].empty():
				self.progressQ[action].get()

		self.progressQ[action].put(int(self.progress[action]))
	#def _callback

	def _remove(self,app_info):
		action='remove'
		flInst=Flatpak.get_system_installations()
		for installer in flInst:
			flRemote=installer.list_remotes()
			remoteInst=installer
			for remote in flRemote:
				remoteName=remote.get_name()
				break
			transaction=Flatpak.Transaction.new_for_installation(installer)
			break
		if transaction:
	   	#Get remote ref
			print(remoteName)
			remoteRef=remoteInst.fetch_remote_ref_sync(remoteName,Flatpak.RefKind.APP,app_info['id'],None,'stable',None)
			print(remoteRef)
			print(app_info['id'])
			#transaction.add_install(remoteName,remoteRef.get_remote_name(),None)
			transaction.add_uninstall(remoteRef.format_ref())
			print(transaction)
			transaction.run()
		app_info['state']='available'
		self._set_status(0)
		return app_info
	#def _remove_snap
def main():
	obj=flatpakHelper()
	return (obj)
