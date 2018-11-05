#The name of the main class must match the file name in lowercase
import os
import urllib
import shutil
import gi
from gi.repository import Gio
gi.require_version ('Snapd', '1')
from gi.repository import Snapd
gi.require_version('AppStreamGlib', '1.0')
from gi.repository import AppStreamGlib as appstream
import time
import html
import threading
from queue import Queue as pool
#Needed for async find method, perhaps only on xenial
wrap=Gio.SimpleAsyncResult()
class snapmanager:
	
	def __init__(self):
		self.dbg=False
		self.progress=0
		self.partial_progress=0
		self.plugin_actions={'install':'snap','remove':'snap','pkginfo':'snap','load':'snap'}
		self.cache_dir=os.getenv("HOME")+"/.cache/lliurex-store"
		self.cache_xmls=self.cache_dir+'/xmls/snap'
		self.cache_last_update=self.cache_xmls+'/.snap.lu'
		self.icons_folder=self.cache_dir+"/icons"
		self.images_folder=self.cache_dir+"/images"
		self.result={}
		self.result['data']={}
		self.result['status']={}
		self.disabled=False
		self.icon_cache_enabled=True
		self.image_cache_enabled=True
		self.cli_mode=False
		if not os.path.isdir(self.icons_folder):
			try:
				os.makedirs(self.icons_folder)
			except:
				self.icon_cache_enabled=False
				#self._debug("Icon cache disabled")
		if not os.path.isdir(self.images_folder):
			try:
				os.makedirs(self.images_folder)
			except:
				self.image_cache_enabled=False
				#self._debug("Image cache disabled")
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		#self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG snap: %s'%msg)
	#def debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def enable(self,state=False):
		self.disabled=state
	#def enable

	def execute_action(self,action,applist=None,store=None,results=0):
		if store:
			self.store=store
		else:
			self.store=appstream.Store()
		self.progress=0
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=''
		
		self.snap_client=Snapd.Client()
		try:
			self.snap_client.connect_sync(None)
		except Exception as e:
			self.disabled=True
			#self._debug("Disabling snap %s"%e)

		if self.disabled==True:
			self._set_status(9)
			self.result['data']=self.store
		else:
			self._check_dirs()
			dataList=[]
			if action=='load':
				self.result['data']=self._load_snap_store(self.store)
			else:
				for app_info in applist:
					self.partial_progress=0
					if action=='install':
						dataList.append(self._install_snap(app_info))
					if action=='remove':
						dataList.append(self._remove_snap(app_info))
					if action=='pkginfo':
						dataList.append(self._get_info(app_info))
					self.progress+=round(self.partial_progress/len(applist),1)
					if self.progress>98:
						self.progress=98
				self.result['data']=list(dataList)
		self.progress=100
		return(self.result)
	#def execute_action

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status

	def _callback(self,client,change, _,user_data):
	    # Interate over tasks to determine the aggregate tasks for completion.
	    total = 0
	    done = 0
	    for task in change.get_tasks():
	        total += task.get_progress_total()
	        done += task.get_progress_done()
	    self.progress = round((done/total)*100)
	#def _callback

	def _check_dirs(self):
		if not os.path.isdir(self.cache_xmls):
			os.makedirs(self.cache_xmls)
	#def _check_dirs

	def _load_snap_store(self,store):
		pkgs=[]
		#Look if cache is up-to-date
		if os.path.isfile(self.cache_last_update):
			epoch_time=time.time()
			fcache=open(self.cache_last_update,'r')
			fcache_update=fcache.read()
			if not fcache_update:
				fcache_update=0
			if int(epoch_time)-int(fcache_update)<86400:
				if os.listdir(os.path.dirname(self.cache_xmls)):
					#self._debug("Loading snap from cache")
					store=self._load_from_cache(store)
					return store

		fcache=open(self.cache_last_update,'w')
		fcache.write(str(int(time.time())))
		pkgs=self._load_sections()
		self._set_status(1)
		store_pool=pool()
		for pkg in pkgs:
			maxconnections = 10
			threads=[]
			semaphore = threading.BoundedSemaphore(value=maxconnections)
			th=threading.Thread(target=self._th_load_store, args = (store_pool,pkg,semaphore))
			threads.append(th)
			th.start()
		for thread in threads:
			try:
				thread.join()
			except:
				pass
		while store_pool.qsize():
			store.add_app(store_pool.get())
		return(store)
	#def _load_snap_store

	def _th_load_store(self,store,pkg,semaphore):
		semaphore.acquire()
		app=self.store.get_app_by_pkgname(pkg.get_name())
		if not app:
			#self._debug("Searching for %s"%pkg.get_name())
			app=self.store.get_app_by_id(pkg.get_name().lower()+".desktop")
			if app:
				bundle=appstream.Bundle()
				bundle.set_kind(bundle.kind_from_string('SNAP'))
				bundle.set_id(pkg.get_name()+'.snap')
				app.add_bundle(bundle)
				app.add_category("Snap")
				store.put(self._generate_appstream_app_from_snap(pkg))
			else:
				store.put(self._generate_appstream_app_from_snap(pkg))
		semaphore.release()
	#def _th_load_store

	def _load_from_cache(self,store):
		for target_file in os.listdir(self.cache_xmls):
			if target_file.endswith('.xml'):
				store_file=Gio.File.new_for_path(self.cache_xmls+'/'+target_file)
				#self._debug("Adding file %s/%s"%(self.cache_xmls,target_file))
				try:
					store.from_file(store_file,'',None)
				except Exception as e:
					#self._debug("Couldn't add file %s to store"%target_file)
					#self._debug("Reason: %s"%e)
					pass
		return store	
	#def _load_from_cache

	def _generate_appstream_app_from_snap(self,pkg):
		bundle=appstream.Bundle()
		app=appstream.App()
		icon=appstream.Icon()
		screenshot=appstream.Screenshot()
#		bundle.set_kind(appstream.BundleKind.SNAP)
		bundle.set_kind(bundle.kind_from_string('SNAP'))
		bundle.set_id(pkg.get_name()+'.snap')
		app.add_bundle(bundle)
		app.set_name("C",pkg.get_name()+'.snap')
		app.add_pkgname(pkg.get_name()+'.snap')
		app.add_category("Snap")
		release=appstream.Release()
		release.set_version(pkg.get_version())
		app.add_release(release)
		app.set_id("io.snapcraft.%s"%pkg.get_name()+'.snap')
		app.set_id_kind=appstream.IdKind.DESKTOP
		app.set_metadata_license("CC0-1.0")
		description="This is an Snap bundle. It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully."
		pkg_description=pkg.get_description()
		pkg_description=html.escape(pkg_description,quote=True)
		pkg_description=pkg_description.replace("<","&gt;")
		app.set_description("C","<p>%s</p><p>%s</p>"%(description,pkg_description))
		app.set_comment("C",pkg.get_summary().rstrip('.'))

		app.add_keyword("C",pkg.get_name())
		for word in pkg.get_summary().split(' '):
			if len(word)>3:
				app.add_keyword("C",word)

		if pkg.get_icon():
			if self.icon_cache_enabled:
				icon.set_kind(appstream.IconKind.LOCAL)
				icon.set_filename(self._download_file(pkg.get_icon(),pkg.get_name(),self.icons_folder))
			else:
				icon.set_kind(appstream.IconKind.REMOTE)
				icon.set_name(pkg.get_icon())
				icon.set_url(pkg.get_icon())
			app.add_icon(icon)

		if pkg.get_license():
			app.set_project_license(pkg.get_license())

		if pkg.get_screenshots():
			for snap_screen in pkg.get_screenshots():
				img=appstream.Image()
				img.set_kind(appstream.ImageKind.SOURCE)
				img.set_url(snap_screen.get_url())
				break
			screenshot.add_image(img)
			app.add_screenshot(screenshot)

		if not os.path.isfile(self.cache_xmls+'/'+app.get_id_filename()):
			xml_path='%s/%s.xml'%(self.cache_xmls,app.get_id_filename())
			gioFile=Gio.File.new_for_path(xml_path)
			app.to_file(gioFile)
			#Fix some things in app_file...
			xml_file=open(xml_path,'r',encoding='utf-8')
			xml_data=xml_file.readlines()
			xml_file.close()
			#self._debug("fixing %s"%xml_path)
			try:
				xml_data[0]=xml_data[0]+"<components>\n"
				xml_data[-1]=xml_data[-1]+"\n"+"</components>"
			except:
				pass
			xml_file=open(xml_path,'w')
			xml_file.writelines(xml_data)
			xml_file.close()
		return(app)
	#def _generate_appstream_app_from_snap

	def _search_cb(self,obj,request,*args):
		global wrap
		wrap=request
	#def _search_cb

	def _load_sections(self):
		sections=self.snap_client.get_sections_sync()
		stable_pkgs=[]
		for section in sections:
			apps=self.snap_client.find_section_sync(Snapd.FindFlags.MATCH_NAME,section,None)
			for pkg in apps:
				stable_pkgs.append(pkg)
		return(stable_pkgs)
	#def _load_sections

	def _search_snap_async(self,tokens,force_stable=True):
		#self._debug("Async Searching %s"%tokens)
		pkgs=None
		global wrap
		self.snap_client.find_async(Snapd.FindFlags.MATCH_NAME,
							tokens,
							None,
							self._search_cb,(None,),None)
		while 'Snapd' not in str(type(wrap)):
			time.sleep(0.1)
		snaps=self.snap_client.find_finish(wrap)
		if type(snaps)!=type([]):
			pkgs=[snaps]
		else:
			pkgs=snaps
		stable_pkgs=[]
		for pkg in pkgs:
			if force_stable:
				if pkg.get_channel()=='stable':
					stable_pkgs.append(pkg)
				else:
					#self._debug(pkg.get_channel())
					pass
			else:
				stable_pkgs.append(pkg)
		return(stable_pkgs)
	#def _search_snap_async

	def _search_snap(self,tokens,force_stable=True):
		#self._debug("Searching %s"%tokens)
		pkg=None
		pkgs=None
		try:
			pkgs=self.snap_client.find_sync(Snapd.FindFlags.MATCH_NAME,tokens,None)
		except Exception as e:
			print("ERR: %s"%e)
			self._set_status(1)
		stable_pkgs=[]
		for pkg in pkgs:
			if force_stable:
				if pkg.get_channel()=='stable':
					stable_pkgs.append(pkg)
				else:
					#self._debug(pkg.get_channel())
					pass
			else:
				stable_pkgs.append(pkg)
		#self._debug("Done")
		return(stable_pkgs)
	#def _search_snap

	def _download_file(self,url,app_name,dest_dir):
		target_file=dest_dir+'/'+app_name+".png"
		if not os.path.isfile(target_file):
			if not os.path.isfile(target_file):
				#self._debug("Downloading %s to %s"%(url,target_file))
				try:
					with urllib.request.urlopen(url) as response, open(target_file, 'wb') as out_file:
						bf=16*1024
						acumbf=0
						file_size=int(response.info()['Content-Length'])
						while True:
							if acumbf>=file_size:
							    break
							shutil.copyfileobj(response, out_file,bf)
							acumbf=acumbf+bf
					st = os.stat(target_file)
				except Exception as e:
					#self._debug("Unable to download %s"%url)
					#self._debug("Reason: %s"%e)
					target_file=''
		return(target_file)
	#def _download_file


	def _get_info(self,app_info):
		#switch to launch async method when running under a gui
		#Request will block when in sync mode under a gui and async mode blocks when on cli (really funny)
		#self._debug("Getting info for %s"%app_info)
		pkg=None
		try:
			pkg=self.snap_client.list_one_sync(app_info['package'].replace('.snap',''))
			app_info['state']='installed'
			pkgs=[pkg]
		except:
			app_info['state']='available'
		if not app_info['size']:
			if self.cli_mode:
				pkgs=self._search_snap(app_info['package'].replace('.snap',''),force_stable=False)
			else:
				pkgs=self._search_snap_async(app_info['package'].replace('.snap',''),force_stable=False)
			#self._debug("Getting extended info for %s %s"%(app_info['package'],pkgs))
			if type(pkgs)==type([]):
				for pkg in pkgs:
					#self._debug("Getting extended info for %s"%app_info['name'])
					if pkg.get_download_size():
						app_info['size']=str(pkg.get_download_size())
					elif pkg.get_installed_size():
						app_info['size']=str(pkg.get_installed_size())
					else:
						app_info['size']="-1"
					break
			else:
				app_info['size']='0'
		#self._debug("Info for %s"%app_info)
		self.partial_progress=100
		return(app_info)
	#def _get_info

	def _install_snap(self,app_info):
		#self._debug("Installing %s"%app_info['name'])
		def install(app_name,flags):
			self.snap_client.install2_sync(flags,app_name.replace('.snap',''),
					None, # channel
					None, #revision
					self._callback, (None,),
					None) # cancellable
			app_info['state']='installed'
			self._set_status(0)

		if app_info['state']=='installed':
			self._set_status(4)
		else:
			try:
				install(app_info['name'],Snapd.InstallFlags.NONE)
			except Exception as e:
				try:
					if e.code==19:
						install(app_info['name'],Snapd.InstallFlags.CLASSIC)
				except Exception as e:
					#self._debug("Install error %s"%e)
					self._set_status(5)
		#self._debug("Installed %s"%app_info)
		return app_info
	#def _install_snap

	def _remove_snap(self,app_info):
		if app_info['state']=='available':
			self._set_status(3)
		else:
			try:
				self.snap_client.remove_sync(app_info['name'].replace('.snap',''),
                       self._callback, (None,),
						None) # cancellable
				app_info['state']='available'
				self._set_status(0)
			except Exception as e:
				print("Remove error %s"%e)
				self._set_status(6)
		return app_info
	#def _remove_snap
