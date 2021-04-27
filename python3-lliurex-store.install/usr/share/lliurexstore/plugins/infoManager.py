import locale
import re
class infomanager:
	def __init__(self):
		self.dbg=False
		self.plugin_actions={'get_info':'*'}
		self.result={}
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=[]
		self.progress=0
		self.inc=0
		self._set_locale()
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		#self._debug ("Debug enabled")
	#def set__debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Info: %s'%msg)
	#def _debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,action,applist,match=False):
		self.progress=0
		count=len(applist)
		if (action=='get_info' or action=='info') and count>0:
			inc=100.0/count
			self.result['data']=self._get_info(applist)
		self.progress=100
		return(self.result)
	#def execute_action
	
	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status

	def _callback_progress(self):
		self.progress=self.progress+self.inc
	#def _callback_progress

	def _set_locale(self):
		if locale.getdefaultlocale()[0]=="ca_ES":
			self.locale=['ca_ES@valencia','ca@valencia','qcv','ca','ca_ES','es_ES','es','en_US','en_GB','en','C']
		else:
			if locale.getdefaultlocale()[0]=="es_ES":
				self.locale=['es_ES','es','ca_ES@valencia','ca@valencia','qcv','ca','ca_ES','en_US','en_GB','en','C']
			else:
				self.locale=[locale.getlocale()[0],'en_US','en_GB','en','ca_ES@valencia','ca@valencia','qcv','ca','es_ES','es','C']
	#def _set_locale

	def _get_info(self,applist):
		applistInfo=[]
		for app in applist:
			appInfo=self._init_appInfo()
			#self._debug("Gathering package info for "+app.get_id())
#Earlier versions stored the appstream_id as the memory dir of the metadata
#Changes in python3.6 and pickle module forces us to disable this feature... 
#			appInfo['appstream_id']=app
			if app.get_id():
				appInfo['id']=app.get_id()
			for localeItem in self.locale:
				if app.get_name(localeItem):
					appInfo['name']=app.get_name(localeItem)
					break
			if app.get_release_default():
				appInfo['version']=app.get_release_default().get_version()
			else:
				for release in app.get_releases():
					appinfo['version']=release.get_version()
					break
			if app.get_pkgname_default():
				appInfo['package']=app.get_pkgname_default()
			if len(app.get_pkgnames())>1:
				appInfo['packages']=app.get_pkgnames()
			if app.get_project_license():
				appInfo['license']=app.get_project_license()
			else:
				appInfo['license']='other/restricted'
				orig=app.get_origin()
				if orig:
					if '-main' in orig or '-universe' in orig:
						appInfo['license']='open source'
			for localeItem in self.locale:
				if app.get_comment(localeItem):
					appInfo['summary']=app.get_comment(localeItem)
					appInfo['summary']=appInfo['summary'].replace('&amp;','&')
					appInfo['summary']=appInfo['summary'].replace('<p>','')
					break
			for localeItem in self.locale:
				if app.get_description(localeItem):
					appInfo['description']=app.get_description(localeItem)
					break
			if app.get_categories():
				appInfo['categories']=app.get_categories()
			if app.get_icon_default():
				if app.get_icon_default().get_filename():
					appInfo['icon']=app.get_icon_default().get_filename()
				else:
					appInfo['icon']=app.get_icon_default().get_name()
				if appInfo['icon']==None:
					icons=app.get_icons()
					if icons:
						for icon in icons:
							appInfo['icon']=icon.get_name()
							break
					else:
						appInfo['icon']=''
			if appInfo['icon']==None:	
				appInfo['icon']=''
			if app.get_screenshots():	
				thumbnails_list=[]
				default_screenshot=''
				screenshots_list=[]
				for screenshot in app.get_screenshots():
					for img in screenshot.get_images():
			#The values are the values of appstream.ImageKind. 1=Source, 2=Thumbnail, 0=UNKNOWN
			#yml currently doen's support unkown images so we assign videos depending on file extension
						if img.get_url():
							if not re.search(r'\.....?$',img.get_url()):
								appInfo['video']=img.get_url()
								continue
							if img.get_kind()==0:	
								appInfo['video']=img.get_url()
								continue
							if img.get_kind()==1: #2=Default;1=normal;0=unknown
								default_screenshot=img.get_url()
								screenshots_list.append(img.get_url())
								continue
							if img.get_kind()==2:	
								thumbnails_list.append(img.get_url())
								continue
						elif img.get_basename():
								screenshots_list.append("/home/lliurex/.cache/lliurex-store/images/"+img.get_basename())

					appInfo['thumbnails']=thumbnails_list
				appInfo['screenshot']=default_screenshot
				appInfo["screenshots"]=screenshots_list
			#The values are the values of appstream.UrlKind. 1=HOMEPAGE, 0=UNKNOWN
#			#self._debug(app.get_url_item(0))
			if app.get_url_item(1):
				appInfo['homepage']=app.get_url_item(1).strip()
			if app.get_url_item(0):
				appInfo['installerUrl']=app.get_url_item(0).strip()
			if app.get_state()==1: #1=Installed
				appInfo['state']='installed'
			else:
				appInfo['state']='available'
			if app.get_kudos():
				appInfo['kudos']=app.get_kudos()
			if app.get_metadata_item('x-zomando'):
				appInfo['installerUrl']=app.get_metadata_item('x-zomando')
			try:
				if app.get_origin():
					appInfo['component']=app.get_origin()
			except Exception as e:
					print ("Error getting origin: %s"%e)
			if app.get_metadata_item('x-video'):
				appInfo['video']=app.get_metadata_item('x-video')
				#Modify the url and create the url embed code
				if 'embed' not in appInfo['video']:
					appInfo['video']=appInfo['video'].replace('watch?v=','embed/')
			#This appstream version returns unknown for all the possible kinds
#			if app.get_bundle_default():
#				appInfo['bundle']=app.get_bundle_default().get_kind()
			#This appstream version returns unknown for all the possible kinds
			#ID must contain bundle type as last field
			for bundle in app.get_bundles():
				if bundle.get_kind()==0:
					kind=bundle.get_id().split('.')[-1]
					appInfo['bundle'].append(kind.lower())
					if kind.lower=='sh':
						appInfo['installerUrl']=bundle.get_id()
			if "flatpak" in appInfo['name']:
					appInfo['bundle'].append("flatpak")

			applistInfo.append(appInfo)
			self._callback_progress()
		self._set_status(0)
		return(applistInfo)
	#def _get_info

	def _init_appInfo(self):
		appInfo={'appstream_id':'',\
		'id':'',\
		'name':'',\
		'version':'',\
		'package':'',\
		'license':'',\
		'summary':'',\
		'description':'',\
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
		'bundle':[],\
		'updatable':'',\
		'component':'',\
		'channel_releases':{}
		}
		return(appInfo)
	#def _init_appInfo

#class infomanager
