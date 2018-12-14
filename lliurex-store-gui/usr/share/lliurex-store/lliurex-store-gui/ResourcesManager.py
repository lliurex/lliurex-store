import urllib.request as urllib2
import os
import tempfile
import datetime
import time
import json
import re
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

HEADER = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11' }


class ResourcesManager:
	
	def __init__(self):
		
		self.distro_name="lliurex"
		self.base_url="http://appstream.ubuntu.com/data/"
		self.icons_url_file="icons-64x64.tar.gz"
		self.icons_path="/var/lib/app-info/icons/"
		self.dists=["xenial","xenial-updates","xenial-security"]
		self.components=["main","restricted","universe","multiverse"]
		self.download_cache="/tmp/lliurex-store-cache/"
		self.icon_dates_file="downloaded_icons.dates"
		
		self.distro_name="ubuntu"
		
		self.icon_db=Gtk.IconTheme()
		self.icon_db.set_custom_theme("Vibrancy-Dark-Orange")
		try:
			self.package_icon=self.icon_db.lookup_icon("package",256,Gtk.IconLookupFlags.FORCE_SVG ).get_filename()
		except:
			self.icon_db.set_custom_theme("Humanity")
			self.package_icon=self.icon_db.lookup_icon("package-x-generic",256,Gtk.IconLookupFlags.FORCE_SVG ).get_filename()

		
	#def init

	def get_icon(self,pkg_info):
		
		debian_name=pkg_info["package"]
		icon=pkg_info["icon"]
		if icon==None:
			icon=""

		if os.path.isfile(icon):
			return(icon)

		if icon.startswith("http"):
			cache_dir=os.getenv("HOME")+"/.cache/lliurex-store/icons"
			icon_name=icon.split("/")[-1]
			if not os.path.exists(cache_dir):
				os.makedirs(cache_dir)
			if os.path.isfile(cache_dir+"/"+icon_name):
				return(cache_dir+"/"+icon_name)
			icon_file=cache_dir+"/"+icon_name
			url=icon
			try:
				req=urllib2.Request(url,headers=HEADER)
				res=urllib2.urlopen(req)
				x=open(icon_file,"wb")
				x.write(res.read())
				x.close()
			except Exception as e:
				icon_file=''
			finally:
				return(icon_file)
	
		
		component=pkg_info["component"]
		ret_icon=self.icon_db.lookup_icon(debian_name,256,Gtk.IconLookupFlags.FORCE_SVG)
		if ret_icon!=None:
			return ret_icon.get_filename()
		
		ret_icon=self.icon_db.lookup_icon(icon,256,Gtk.IconLookupFlags.FORCE_SVG)
		if ret_icon!=None:
			return ret_icon.get_filename()
			
		
		if len(icon)>0:
		
			for dist in ["xenial-updates","xenial-security","xenial"]:
				# "64x64/" is included in pkg_info["icon"]
#				if "64x64/" not in icon:
				if not re.match("[0-9]*x[0-9]*\/",icon):
					icon="64x64/" + icon
					if debian_name+"_"+debian_name not in icon:
						icon=icon.replace(debian_name,debian_name+"_"+debian_name)
						if not icon.endswith(".png"):
							icon=icon+'.png'
					if "pyromaths" in icon:
						icon="64x64/pyromaths_pyromaths.png"
					
				ret_icon=self.icons_path+"%s/%s"%(component,icon)
				if os.path.exists(ret_icon):
					return ret_icon
				else:
					ret_icon=ret_icon.replace("64x64","128x128")
					if os.path.exists(ret_icon):
						return ret_icon
					icon="64x64/" + pkg_info['icon']
				ret_icon=self.icons_path+"%s/%s"%(component,icon)
				if os.path.exists(ret_icon):
					return ret_icon
				else:
				#Last attempt
					if len(pkg_info['id'].split('.'))>2:
						pkg_id=pkg_info['id'].split('.')[-2]
						icon="64x64/%s_%s.png"%(debian_name,pkg_id)
				ret_icon=self.icons_path+"%s/%s"%(component,icon)
				if os.path.exists(ret_icon):
					return ret_icon
				else:
				#Unaccurate icon search... 
					if os.path.isdir(self.icons_path+"/"+component+"/64x64"):
						for icon_file in os.listdir(self.icons_path+"/"+component+"/64x64/"):
							if re.search("^.*"+pkg_info['icon']+".*\.png",icon_file):
								ret_icon=self.icons_path+"%s/64x64/%s"%(component,icon_file)
				if os.path.exists(ret_icon):
					return ret_icon
				else:
				#The very last attempt. We'll look for the icon in the desktop (if any)
					desktop_file=pkg_info['id']
					if not desktop_file.endswith(".desktop"):
						desktop_file=desktop_file+".desktop"
					if os.path.isfile("/usr/share/applications/%s"%desktop_file):
						f=open("/usr/share/applications/%s"%desktop_file,'r')
						for l in f.readlines():
							if l.startswith("Icon"):
								icon_name=l.split('=')[-1].strip('\n')
								if os.path.isfile(icon_name):
									return(icon_name)
								else:
									ret_icon=self.icon_db.lookup_icon(icon_name,256,Gtk.IconLookupFlags.FORCE_SVG)
									if ret_icon:
										return(ret_icon.get_filename())

		ret_icon=self.package_icon
		return ret_icon
		
	#def get_icon

	
	def check_perms(self):
		
		try:
			f=open("/run/lliurex-store.background.pid","w")
			f.close()
			return True
			
		except:
			return False
			
	#def check_perms
	
	
	def create_icons_dir(self):
		
		if not os.path.exists(self.icons_path):
			os.makedirs(self.icons_path)
			
	#def create_icons_dir
	
	
	def write_local_icons_info(self,info):
		
		f=open(self.icon_dates_file,"w")
		f.write(json.dumps(info,indent=4))
		f.close()
		
	#def write_local_icons_info
	
	
	def check_local_icons_files(self):
		
		self.local_icons_dates={}
		try:
			f=open(self.icon_dates_file)
			self.local_icons_dates=json.load(f)
			f.close()
		except Exception as e:
			print(e)
		
		for dist in self.dists:
			self.local_icons_dates.setdefault(dist,{})
			for component in self.components:
				self.local_icons_dates[dist].setdefault(component,-1)

	#def check_local_icons_files


	
	def check_remote_icons_files(self):
		
		self.remote_icons_dates={}
		
		for dist in self.dists:
			self.remote_icons_dates[dist]={}
			for component in self.components:
				
				url=self.base_url+dist+"/"+component
					
				try:
					
					req=urllib2.Request(url,headers=HEADER)
					res=urllib2.urlopen(req)
					x=tempfile.NamedTemporaryFile()
					x.write(res.read())
					x.seek(0)
					
					for line in x.readlines():
						line=line.decode("utf-8")
						if self.icons_url_file in line:
							line=line.split('<td align="right">')[1].split(" ")
							icons_date=line[0]
							icons_date=time.mktime(datetime.datetime.strptime(icons_date, "%Y-%m-%d").timetuple())
							self.remote_icons_dates[dist][component]=icons_date
							break
					x.close()
						
				except Exception as e:
					pass
					
				if component not in self.remote_icons_dates[dist]:
					self.remote_icons_dates[dist][component]=-1
	
	#def download_home_info
	
	
	def update_icons(self):
		
		self.check_local_icons_files()
		self.check_remote_icons_files()
		
		self.current_icons_dates={}
		
		if not os.path.exists(self.download_cache):
			os.makedirs(self.download_cache)
	
		for dist in self.dists:
			self.current_icons_dates[dist]={}
			for component in self.components:
			
				if self.remote_icons_dates[dist][component] > self.local_icons_dates[dist][component]:

					url=self.base_url+dist+"/"+component+"/"+self.icons_url_file
					try:
						icon_file=self.download_cache+"%s_%s_icons.tar.gz"%(dist,component)
						path=self.icons_path+self.distro_name+"-"+dist+"-"+component+"/64x64/"
						
						req=urllib2.Request(url,headers=HEADER)
						res=urllib2.urlopen(req)
						x=open(icon_file,"wb")
						x.write(res.read())
						x.close()
						
						self.current_icons_dates[dist][component]=self.remote_icons_dates[dist][component]
						
						command="tar -xf %s -C %s"%(icon_file,path)
						if not os.path.exists(path):
							os.makedirs(path)
						
						os.system(command)
						
						
					except Exception as e:
						self.current_icons_dates[dist][component]=self.local_icons_dates[dist][component]
						
				else:
					self.current_icons_dates[dist][component]=self.local_icons_dates[dist][component]
		
	#def update_icons
	
	
#class ResourcesManager


if __name__=="__main__":
	
	rm=ResourcesManager()
	#rm.check_remote_icons_files()
	#rm.check_local_icons_files()
	rm.update_icons()
	pkg={}
	pkg["package"]="zsnes"
	pkg["component"]="universe"
	pkg["icon"]="64x64/zsnes_zsnes.png"
	
	print(rm.get_icon(pkg))
	


