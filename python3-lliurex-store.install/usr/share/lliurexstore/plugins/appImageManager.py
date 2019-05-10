#The name of the main class must match the file name in lowercase
import re
import urllib
from urllib.request import Request
from urllib.request import urlretrieve
import shutil
import json
import os
import sys
import threading
import queue
import time
import random
import gi
from gi.repository import Gio
gi.require_version('AppStreamGlib', '1.0')
from gi.repository import AppStreamGlib as appstream
from bs4 import BeautifulSoup
# -*- coding: utf-8 -*-
#from subprocess import call

class appimagemanager:
	def __init__(self):
		self.dbg=False
		self.progress=0
		self.partial_progress=0
		self.plugin_actions={'install':'appimage','remove':'appimage','pkginfo':'appimage','load':'appimage'}
		self.result={}
		self.result['data']={}
		self.result['status']={}
		self.cache_dir=os.getenv("HOME")+"/.cache/lliurex-store"
		self.icons_dir=self.cache_dir+"/icons"
		self.cache_xmls=self.cache_dir+"/xmls/appimage"
		self.appimage_dir=os.getenv("HOME")+"/AppImages"
		#Prevent appimage desktop integration
		if not os.path.isfile("%s/.local/share/appimagekit/no_desktopintegration"%os.environ['HOME']):
			try:
				os.makedirs("%s/.local/share/appimagekit/"%os.environ['HOME'])
			except:
				pass
			f.open("%s/.local/share/appimagekit/no_desktopintegration"%os.environ['HOME'],'w')
			f.close()
		#To get the description of an app we must go to a specific url defined in url_info.
		#$(appname) we'll be replaced with the appname so the url matches the right one.
		#If other site has other url naming convention it'll be mandatory to define it with the appropiate replacements
		self.repos={'appimagehub':{'type':'json','url':'https://appimage.github.io/feed.json','url_info':''}}
		#Appimges not stored in a repo must be listed in this file, providing the download url and the info url (if there's any)
		self.external_appimages="/usr/share/lliurex-store/files/external_appimages.json"
		self.locale=['ca_ES@valencia','ca@valencia','qcv','ca','ca_ES','es_ES','es','en_US','en_GB','en','C']
		self.disabled=False
		self.icon_cache_enabled=True
		self.image_cache_enabled=True
		self.cache_last_update=self.cache_xmls+'/.appimage.lu'
		self.apps_for_store=queue.Queue()
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		#self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG appimage: %s'%msg)
	#def debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def enable(self,state=False):
		self.disable=state
	#def enable

	def execute_action(self,action,applist=None,store=None):
		if store:
			self.store=store
		else:
			self.store=appstream.Store()
		self.appimage_store=appstream.Store()
		self.progress=0
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=[]
		self.threads=[]
		dataList=[]
		if self.disabled:
			self._set_status(9)
			self.result['data']=self.store
		else:
			self._chk_installDir()
			if action=='load':
				self._load_appimage_store(self.store)
				#self._debug("Ending threads...")
				while not self.apps_for_store.empty():
					app=self.apps_for_store.get()
					self.store.add_app(app)
				self.result['data']=self.store
			else:
				for app_info in applist:
					self.partial_progress=0
					if action=='install':
						dataList.append(self._install_appimage(app_info))
					if action=='remove':
						dataList.append(self._remove_appimage(app_info))
					if action=='pkginfo':
						dataList.append(self._get_info(app_info))
					self.progress+=int(self.partial_progress/len(applist))-1
				self.result['data']=list(dataList)
		self.progress=100
		return(self.result)
	#def execute_action

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status

	def _callback(self,partial_size=0,total_size=0):
		limit=99
		if partial_size!=0 and total_size!=0:
			inc=round(partial_size/total_size,2)*100
			self.progress=inc
		else:
			inc=1
			margin=limit-self.progress
			inc=round(margin/limit,3)
			self.progress=(self.progress+inc)
		if (self.progress>limit):
			self.progress=limit
	#def _callback

	def _chk_installDir(self):
		msg_status=True
		if not os.path.isdir(self.appimage_dir):
			try:
				os.makedirs(self.appimage_dir)
			except:
				msg_status=False
		return msg_status				
	#def _chk_installDir

	def _install_appimage(self,app_info):
		app_info=self._get_info(app_info,force=True)
		#self._debug("Installing %s"%app_info)
		if app_info['state']=='installed':
			self._set_status(4)
		else:
			if 'appimage' in app_info['channel_releases'].keys():
				appimage_url=app_info['channel_releases']['appimage'][0]
			else:
				#self._debug("No url in: %s"%app_info['channel_releases'])
				pass
			#self._debug("Downloading "+appimage_url)
			dest_path=self.appimage_dir+'/'+app_info['package']
			if appimage_url:
				try:
					req=Request(appimage_url, headers={'User-Agent':'Mozilla/5.0'})
					with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
						bf=16*1024
						acumbf=0
						app_size=int(response.info()['Content-Length'])
						while True:
							if acumbf>=app_size:
							    break
							shutil.copyfileobj(response, out_file,bf)
							acumbf=acumbf+bf
							self._callback(acumbf,app_size)
					st = os.stat(dest_path)
					os.chmod(dest_path, st.st_mode | 0o755)
					self._set_status(0)
				except Exception as e:
					print(e)
					self._set_status(5)
			else:
				self._set_status(12)
		return app_info
	#def _install_appimage

	def _remove_appimage(self,app_info):
		#self._debug("Removing "+app_info['package'])
		if os.path.isfile(self.appimage_dir+'/'+app_info['package']):
			try:
				call([self.appimage_dir+"/"+app_info['package'], "--remove-appimage-desktop-integration"])
			except:
				pass
			try:
				os.remove(self.appimage_dir+"/"+app_info['package'])
				self._set_status(0)
			except:
				self._set_status(6)
		return(app_info)
	#def _remove_appimage

	def _load_appimage_store(self,store):
		#Look if cache is up-to-date
		sw_update_cache=True
		if os.path.isfile(self.cache_last_update):
			epoch_time=time.time()
			fcache=open(self.cache_last_update,'r')
			fcache_update=fcache.read()
			if not fcache_update:
				fcache_update=0
			if int(epoch_time)-int(fcache_update)<86400:
				if os.listdir(os.path.dirname(self.cache_xmls)):
					#self._debug("Loading appimage from cache")
					sw_update_cache=False
		if sw_update_cache:
			self._get_bundles_catalogue()
			self._get_external_catalogue()
			fcache=open(self.cache_last_update,'w')
			fcache.write(str(int(time.time())))
		if os.path.exists(self.cache_xmls):
			#self._debug("Loading appimage catalog")
			store=self._generic_file_load(self.cache_xmls,store)
		return(store)
	#def load_bundles_catalog(self)
	
	def _generic_file_load(self,target_path,store):
		icon_path='/usr/share/icons/hicolor/128x128'
		if not os.path.isdir(target_path):
			os.makedirs(target_path)
		files=os.listdir(target_path)
		for target_file in os.listdir(target_path):
			if target_file.endswith('.xml'):
				store_path=Gio.File.new_for_path(target_path+'/'+target_file)
				#self._debug("Adding file "+target_path+'/'+target_file)
				try:
					store.from_file(store_path,icon_path,None)
				except Exception as e:
					#self._debug("Couldn't add file "+target_file+" to store")
					#self._debug("Reason: "+str(e))
					pass
		return(store)
	#def _generic_file_load

	def _get_bundles_catalogue(self):
		applist=[]
		appdict={}
		all_apps=[]
		outdir=self.cache_xmls
		#Load repos
		for repo_name,repo_info in self.repos.items():
			if not os.path.isdir(self.cache_xmls):
				try:
					os.makedirs(self.cache_xmls)
				except:
					#self._debug("appImage catalogue could not be fetched: Permission denied")
					pass
			#self._debug("Fetching repo %s"%repo_info['url'])
			if repo_info['type']=='json':
				applist=self._process_appimage_json(self._fetch_repo(repo_info['url']),repo_name)

			#self._debug("Fetched repo "+repo_info['url'])
			self._th_generate_xml_catalog(applist,outdir,repo_info['url_info'],repo_info['url'],repo_name)
			all_apps.extend(applist)
		return True

	def _get_external_catalogue(self):
		applist=[]
		all_apps=[]
		outdir=self.cache_xmls
		#Load external apps
		for app_name,app_info in self._get_external_appimages().items():
			if os.path.isdir(self.cache_xmls):
				appinfo=self._init_appinfo()
				if 'name' in app_info.keys():
					appinfo['name']=app_info['name']
				else:
					appinfo['name']=app_info['url'].split('/')[-1]
				appinfo['package']=app_info['url'].split('/')[-1]
				if 'homepage' in app_info.keys():
					appinfo['homepage']=app_info['homepage']
				else:
					appinfo['homepage']='/'.join(app_info['url'].split('/')[0:-1])
				appinfo['installerUrl']=app_info['url']
				if 'description' in app_info.keys():
					if type(app_info['description'])==type({}):
						for lang in app_info['description']:
							appinfo['description'].update({lang:app_info['description'][lang]})
					else:
						appinfo['description'].update({"C":appimage['description']})
				if 'categories' in app_info.keys():
					appinfo['categories']=app_info['categories']
				if 'keywords' in app_info.keys():
					appinfo['keywords']=app_info['keywords']
				if 'version' in app_info.keys():
					appinfo['reywords']=app_info['keywords']
				#self._debug("Fetching external appimage %s"%app_info['url'])
				appinfo['bundle']='appimage'
				#self._debug("External:\n%s\n-------"%appinfo)
				applist.append(appinfo)
			else:
				#self._debug("External appImage could not be fetched: Permission denied")
				pass
		self._th_generate_xml_catalog(applist,outdir,app_info['url_info'],app_info['url'],app_name)
		#self._debug("Fetched appimage "+app_info['url'])
		all_apps.extend(applist)
		#self._debug("Removing old entries...")
#		self._clean_bundle_catalogue(all_apps,outdir)
		return(True)
	#def _get_bundles_catalogue
	
	def _fetch_repo(self,repo):
		content=''
		req=Request(repo, headers={'User-Agent':'Mozilla/5.0'})
		with urllib.request.urlopen(req) as f:
			content=(f.read().decode('utf-8'))
		
		return(content)
	#def _fetch_repo
	
	def _get_external_appimages(self):
		external_appimages={}
		if os.path.isfile(self.external_appimages):
			try:
				with open(self.external_appimages) as appimages:
					external_appimages=json.load(appimages)
			except:
				#self._debug("Can't load %s"%self.external_appimages)
				pass
		return external_appimages
	#def _get_external_appimages
	
	def _process_appimage_json(self,data,repo_name):
		applist=[]
		json_data=json.loads(data)
		if 'items' in json_data.keys():
			for appimage in json_data['items']:
				appinfo=self._th_process_appimage(appimage)
				if appinfo:
					applist.append(appinfo)
		return (applist)
	#_process_appimage_json

	def _th_process_appimage(self,appimage):
		appinfo=None
		releases=[]
		if 'links' in appimage.keys():
			if appimage['links']:
				appinfo=self.load_json_appinfo(appimage)
		return(appinfo)
        #def _th_process_appimage

	def load_json_appinfo(self,appimage):
		#self._debug(appimage)
		appinfo=self._init_appinfo()
		appinfo['name']=appimage['name']
		appinfo['package']=appimage['name']
		if 'license' in appimage.keys():
			appinfo['license']=appimage['license']
		appinfo['summary']=''
		if 'description' in appimage.keys():
			if type(appimage['description'])==type({}):
				for lang in appinfo['description'].keys():
					appinfo['description'].update({lang:appimage['description'][lang]})
			else:
				appinfo['description']={"C":appimage['description']}
		if 'categories' in appimage.keys():
			appinfo['categories']=appimage['categories']
		if 'icon' in appimage.keys():
			appinfo['icon']=appimage['icon']
		if 'icons' in appimage.keys():
			#self._debug("Loading icon %s"%appimage['icons'])
			if appimage['icons']:
				#self._debug("Loading icon %s"%appimage['icons'][0])
				appinfo['icon']=appimage['icons'][0]
		if 'screenshots' in appimage.keys():
			appinfo['thumbnails']=appimage['screenshots']
		if 'links' in appimage.keys():
			if appimage['links']:
				for link in appimage['links']:
					if 'url' in link.keys() and link['type']=='Download':
						appinfo['installerUrl']=link['url']
		if 'authors' in appimage.keys():
			if appimage['authors']:
				for author in appimage['authors']:
					if 'url' in author.keys():
						#self._debug("Author: %s"%author['url'])
						appinfo['homepage']=author['url']
		else:
			appinfo['homepage']='/'.join(appinfo['installerUrl'].split('/')[0:-1])
		appinfo['bundle']=['appimage']
		return appinfo
	#def load_json_appinfo

	def _th_generate_xml_catalog(self,applist,outdir,info_url,repo,repo_name):
		maxconnections = 2
		threads=[]
		semaphore = threading.BoundedSemaphore(value=maxconnections)
		random_applist = list(applist)
		random.shuffle(random_applist)
		for app in applist:
			th=threading.Thread(target=self._th_write_xml, args = (app,outdir,info_url,repo,repo_name,semaphore))
			threads.append(th)
			th.start()
		for thread in threads:
			thread.join()
	#def _th_generate_xml_catalog

	def	_th_write_xml(self,appinfo,outdir,info_url,repo,repo_name,semaphore):
		semaphore.acquire()
		self._add_appimage(appinfo)
		semaphore.release()
	#def _th_write_xml

	def _add_appimage(self,appinfo):
		#Search in local store for the app
		sw_new=True
		app=appstream.App()
		app_orig=self.store.get_app_by_pkgname(appinfo['name'].lower())
		if not app_orig:
			app_orig=self.store.get_app_by_id(appinfo['name'].lower()+".desktop")
		if app_orig:
			#self._debug("Extending app %s"%appinfo['package'])
			if appinfo['icon']:
				#self._debug("Icon: %s"%appinfo['icon'])
				app=self._copy_app_from_appstream(app_orig,app,copy_icon=False)
			else:
				app=self._copy_app_from_appstream(app_orig,app,copy_icon=True)
			sw_new=False
		else:
			#self._debug("Generating new %s"%appinfo['package'])
			pass
		if appinfo['name'].lower().endswith('.appimage'):
			app.set_id("appimagehub.%s"%appinfo['name'].lower())
			app.set_name("C",appinfo['name'])
		else:
			app.set_id("appimagehub.%s"%appinfo['name'].lower()+'.appimage')
			app.set_name("C",appinfo['name']+".appimage")
		if appinfo['package'].lower().endswith('.appimage'):
			app.add_pkgname(appinfo['package'].lower())
		else:
			app.add_pkgname(appinfo['package'].lower()+".appimage")
		app.set_id_kind=appstream.IdKind.DESKTOP

		if appinfo['license']:
			app.set_project_license(appinfo['license'])
		bundle=appstream.Bundle()
		bundle.set_kind(bundle.kind_from_string('APPIMAGE'))
		if appinfo['package'].endswith('.appimage'):
			bundle.set_id(appinfo['package'])
		else:
			bundle.set_id(appinfo['package']+'.appimage')
		app.add_bundle(bundle)
		if 'keywords' in appinfo.keys():
			for keyword in appinfo['keywords']:
				app.add_keyword("C",keyword)
			if 'appimage' not in appinfo['keywords']:
				app.add_keyword("C","appimage")
		else:
			app.add_keyword("C","appimage")
		app.add_url(appstream.UrlKind.UNKNOWN,appinfo['installerUrl'])
		app.add_url(appstream.UrlKind.HOMEPAGE,appinfo['homepage'])
		if sw_new:
			app.add_keyword("C",appinfo['package'])
			if not appinfo['name'].endswith('.appimage'):
				app.set_name("C",appinfo['name']+".appimage")
			desc_header="This is an AppImage bundle of app %s. It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully."%appinfo['name']
			if appinfo['description']:
				for lang,desc in appinfo['description'].items():
					desc=desc.replace('&','&amp;')
					description="<p>%s</p><p>%s</p>"%(desc_header,desc)
					summary=' '.join(list(desc.split(' ')[:10]))
					app.set_description(lang,description)
					app.set_comment(lang,summary)
			else:
				description="<p>%s</p>"%(desc_header)
				summary=' '.join(list(desc_header.split(' ')[:8]))
				app.set_description("C",description)
				app.set_comment("C",summary)

			if 'categories' in appinfo.keys():
				for category in appinfo['categories']:
					app.add_category(category)
				if 'appimage' not in appinfo['categories']:
					app.add_category("appimage")
			else:
				app.add_category("appimage")
		if appinfo['icon']:
			icon=appstream.Icon()
			if self.icon_cache_enabled:
				icon.set_kind(appstream.IconKind.LOCAL)
				icon_fn=self._download_file(appinfo['icon'],appinfo['name'],self.icons_dir)
				icon.set_filename(icon_fn)
			else:
				icon.set_kind(appstream.IconKind.REMOTE)
				icon.set_name(pkg.get_icon())
				icon.set_url(pkg.get_icon())
			app.add_icon(icon)
		if appinfo['thumbnails']:
			screenshot=appstream.Screenshot()
			img=appstream.Image()
			if not appinfo['thumbnails'][0].startswith('http'):
					appinfo['screenshot']=appinfo['thumbnails'][0]
					appinfo['screenshot']="https://appimage.github.io/database/%s"%appinfo['screenshot']
			img.set_kind(appstream.ImageKind.SOURCE)
			img.set_url(appinfo['screenshot'])
			screenshot.add_image(img)
			app.add_screenshot(screenshot)
		#Adds the app to the store
		self.apps_for_store.put(app)
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
				xml_data[0]=xml_data[0]+"<components origin=\"%s\">\n"%app.get_origin()
				xml_data[-1]=xml_data[-1]+"\n"+"</components>"
			except:
				pass
			xml_file=open(xml_path,'w')
			xml_file.writelines(xml_data)
			xml_file.close()
	#def _add_appimage

	def _copy_app_from_appstream(self,app_orig,app,copy_icon=True):
		desc_header="This is an AppImage bundle of app %s. It hasn't been tested by our developers and comes from a 3rd party dev team. Please use it carefully."%app_orig.get_pkgnames()[0]
		app.set_id("appimage."+app_orig.get_id())
		for category in app_orig.get_categories():
			app.add_category(category)
		app.add_category("appimage")
		for screenshot in app_orig.get_screenshots():
			app.add_screenshot(screenshot)
		if copy_icon:
			for icon in app_orig.get_icons():
				app.add_icon(icon)
		for localeItem in self.locale:
			if app_orig.get_name(localeItem):
				app.set_name(localeItem,app_orig.get_name(localeItem)+".appimage")
			if app_orig.get_description(localeItem):
				app.set_description(localeItem,"<p>%s</p><p>%s</p>"%(desc_header,app_orig.get_description(localeItem)))
			if app_orig.get_comment(localeItem):
				app.set_comment(localeItem,app_orig.get_comment(localeItem))
		app.set_origin(app_orig.get_origin())
		return app
	#def _copy_app_from_appstream

	def _clean_bundle_catalogue(self,applist,outdir):
		xml_files_list=[]
		applist=[item.lower() for item in applist]
		for xml_file in os.listdir(outdir):
			if xml_file.endswith('.xml'):
				xml_files_list.append(xml_file.lower().replace('.xml','appimage'))
	
		if xml_files_list:
			xml_discard_list=list(set(xml_files_list).difference(applist))
			for discarded_file in xml_discard_list:
				os.remove(outdir+'/'+discarded_file.replace('appimage','.xml'))
	#def _clean_bunlde_catalogue

	def _download_file(self,url,app_name,dest_dir):
		target_file=dest_dir+'/'+app_name+".png"
		if not url.startswith('http'):
			url="https://appimage.github.io/database/%s"%url
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
	
	def _chk_bundle_dir(self,outdir):
		msg_status=True
		if not os.path.isdir(outdir):
			try:
				os.makedirs(outdir)
			except Exception as e:
				msg_status=False
				print(e)
		return(os.access(outdir,os.W_OK|os.R_OK|os.X_OK|os.F_OK))
	#def _chk_bundle_dir
	
	def _init_appinfo(self):
		appInfo={'appstream_id':'',\
		'id':'',\
		'name':'',\
		'version':'',\
		'channel_releases':{},\
		'component':'',\
		'package':'',\
		'license':'',\
		'summary':'',\
		'description':{},\
		'categories':[],\
		'icon':'',\
		'screenshot':'',\
		'thumbnails':[],\
		'video':'',\
		'homepage':'',\
		'installerUrl':'',\
		'state':'',\
		'depends':'',\
		'kudos':'',\
		'suggests':'',\
		'extraInfo':'',\
		'size':'',\
		'bundle':'',\
		'updatable':'',\
		}
		return(appInfo)
	#def _init_appinfo
	
	def _get_info(self,app_info,force=False):
		#self._debug("Searching for %s in %s"%(app_info['package'],self.appimage_dir))
		app_info['state']='available'
		if os.path.isfile(self.appimage_dir+'/'+app_info['package']):
			app_info['state']='installed'
		if not app_info['size'] or force:
			if app_info['installerUrl']:
				#self._debug("installer: %s"%app_info['installerUrl'])
				app_info['channel_releases']={'appimage':[]}
				app_info['channel_releases']['appimage']=self._get_releases(app_info)
			#Get size
			app_info['size']="0"
			app_info['version']='unknown'
			if 'appimage' in app_info['channel_releases'].keys():
				if len(app_info['channel_releases']['appimage'])>0:
					if app_info['channel_releases']['appimage'][0]:
						appimage_url=app_info['channel_releases']['appimage'][0]
						dest_path=self.appimage_dir+'/'+app_info['package']
						if appimage_url:
							try:
								with urllib.request.urlopen(appimage_url) as response:
									app_info['size']=str((response.info()['Content-Length']))
							except:
								app_info['size']="0"
					#Version (unaccurate aprox)
					app_info['version']=app_info['channel_releases']['appimage'][0].split('/')[-2]

		self._set_status(0)
		self.partial_progress=100
		return(app_info)
	#def _get_info

	def _get_releases(self,app_info):
		releases=[]
		releases_page=''
		#self._debug("Info url: %s"%app_info['installerUrl'])
		url_source=""
		try:
			if 'github' in app_info['installerUrl']:
				releases_page="https://github.com"
			if 'gitlab' in app_info['installerUrl']:
				releases_page="https://gitlab.com"
			if 'opensuse' in app_info['installerUrl'].lower():
				releases_page=""
				url_source="opensuse"
#				app_info['installerUrl']=app_info['installerUrl']+"/download"

			if (url_source or releases_page) and not app_info['installerUrl'].lower().endswith(".appimage"):
				content=''
				with urllib.request.urlopen(app_info['installerUrl']) as f:
					try:
						content=f.read().decode('utf-8')
					except:
						#self._debug("UTF-8 failed")
						pass
					soup=BeautifulSoup(content,"html.parser")
					package_a=soup.findAll('a', attrs={ "href" : re.compile(r'.*\.[aA]pp[iI]mage$')})

					for package_data in package_a:
						if url_source=="opensuse":
							package_name=package_data.findAll('a', attrs={"class" : "mirrorbrain-btn"})
						else:
							package_name=package_data.findAll('strong', attrs={ "class" : "pl-1"})
						package_link=package_data['href']
						if releases_page or url_source:
							package_link=releases_page+package_link
							releases.append(package_link)
							#self._debug("Link: %s"%package_link)
			if releases==[]:
				releases=[app_info['installerUrl']]
		except Exception as e:
			#self._debug(e)
			pass
		#self._debug(releases)
		return releases
	#def _get_releases
	
