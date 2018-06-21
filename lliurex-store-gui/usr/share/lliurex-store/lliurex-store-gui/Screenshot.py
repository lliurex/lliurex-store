import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,GdkPixbuf,GLib,GObject
import urllib.request as urllib2
import threading
import os
import ImageManager
import Core
import string
import random

class ScreenshotNeo(Gtk.Stack):
	
	def __init__(self):
		
		Gtk.Stack.__init__(self)
		self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
		self.set_transition_duration(250)
		
		try:
			cache_dir=os.environ["XDG_CACHE_HOME"]
		except:
			cache_dir=os.path.expanduser("~/.cache/")
		
		self.image_dir=cache_dir+"/lliurex-store/"
		
		if not os.path.exists(self.image_dir):
			os.makedirs(self.image_dir)
		
		self.spinner=Gtk.Spinner()
		self.spinner.start()
		
		hbox=Gtk.HBox()
		hbox.pack_start(self.spinner,True,True,0)
		
		self.image=Gtk.Image()
		self.add_titled(hbox,"spinner","Spinner")
		self.add_titled(self.image,"image","Image")
		
		self.image_info={}
		self.image_info["image_url"]=None
		self.image_info["video_url"]=None
		self.image_info["image_id"]=None
		self.image_info["package"]=None
		self.image_info["image_path"]=None
		self.image_info["x"]=-1
		self.image_info["y"]=-1
		self.image_info["aspect_ratio"]=True
		self.image_info["custom_frame"]=False
		self.image_info["force_label"]=False
		self.image_info["pixbuf"]=None
		
		self.show_all()
		
	#def init
	
	
	def set_image_info(self,image_info):
		
		self.image_info["package"]=image_info.setdefault("package","")
		self.image_info["name"]=image_info.setdefault("name","")
		self.image_info["image_path"]=image_info.setdefault("image_path","")
		self.image_info["x"]=image_info.setdefault("x",-1)
		self.image_info["y"]=image_info.setdefault("y",-1)
		self.image_info["aspect_ratio"]=image_info.setdefault("aspect_ratio",True)
		self.image_info["pixbuf"]=image_info.setdefault("pixbuf",None)
		self.image_info["image_url"]=image_info.setdefault("image_url","")
		self.image_info["image_id"]=image_info.setdefault("image_id",self.get_random_id())
		self.image_info["custom_frame"]=image_info.setdefault("custom_frame",False)
		self.image_info["force_label"]=image_info.setdefault("force_label",False)
		
	#def set_image_info
	
	
	def get_random_id(self):
		
		chars=string.ascii_lowercase
		size=10
		return ''.join(random.choice(chars) for _ in range(size))
		
	#def get_random_id
	
	
	def set_from_file(self,image_info):
		
		
		self.set_image_info(image_info)
		
		x=self.image_info["x"]
		y=self.image_info["y"]
		aspect_ratio=self.image_info["aspect_ratio"]
		file_path=self.image_info["image_path"]
		
		if os.path.exists(file_path):
			
			if x==-1 and y==-1:
			
				self.image.set_from_file(file_path)
				pixbuf=self.image.get_pixbuf()
				self.image_info["x"]=pixbuf.get_width()
				self.image_info["y"]=pixbuf.get_height()
				self.set_visible_child_name("image")
				return True
				
			else:
				
				tmp=ImageManager.scale_image(file_path,x,y,aspect_ratio)
				pixbuf=tmp.get_pixbuf()
				self.image_info["x"]=pixbuf.get_width()
				self.image_info["y"]=pixbuf.get_height()
				self.image.set_from_pixbuf(tmp.get_pixbuf())
				self.set_visible_child_name("image")
				return True
			
		return False
		
	#def set_from_file
	
	
	def get_size(self):
		
		print(self.image_info["x"])
		print(self.image_info["y"])
		
	#def get_size
	
	
	def set_from_pixbuf(self,image_info):
		
		self.set_image_info(image_info)		
		
		x=self.image_info["x"]
		y=self.image_info["x"]
		pixbuf=self.image_info["pixbuf"]
		aspect_ratio=self.image_info["aspect_ratio"]
		
		if pixbuf!=None:
			
			if x==-1 and y==-1:
				
				self.image.set_from_pixbuf(pixbuf)
				self.image_info["x"]=pixbuf.get_width()
				self.image_info["y"]=pixbuf.get_height()
				self.set_visible_child_name("image")
				
			else:
				
				pixbuf=ImageManager.scale_pixbuf(pixbuf,x,y,aspect_ratio)
				self.image.set_from_pixbuf(pixbuf)
				self.image_info["x"]=pixbuf.get_width()
				self.image_info["y"]=pixbuf.get_height()
				self.set_visible_child_name("image")
			
		
			return True

		return False		
		
	#set_from_pixbuf
	
	
	def wait_for_image(self):
	
		while self.thread.is_alive():
			return True
		
		
		if os.path.exists(self.image_dir+self.image_info["image_id"]):
			self.set_from_file(self.image_info)
		
		return False
	
	#def _download
	
	
	def download_image(self,image_info):
		
		self.set_image_info(image_info)	
		
		x=self.image_info["x"]
		y=self.image_info["y"]
		
		self.set_visible_child_name("spinner")
		
		self.spinner.set_size_request(x,y)
		GLib.timeout_add(500,self.wait_for_image)
		
		self.thread=threading.Thread(target=self.download_image_thread)
		self.thread.daemon=True
		self.thread.start()
		
	#def download_image
	
	
	def download_image_thread(self):
		
		if not os.path.exists(self.image_dir+self.image_info["image_id"]):
			
			header = {
					'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
				}
			
			try:
			
				self.image_info["image_path"]=self.image_dir+self.image_info["image_id"]
				req=urllib2.Request(self.image_info["image_url"],headers=header)
				res=urllib2.urlopen(req)
				f=open(self.image_dir+self.image_info["image_id"],"wb")
				f.write(res.read())
				f.close()
				
				
				if self.image_info["custom_frame"] or self.image_info["force_label"]:
					ImageManager.create_banner(self.image_dir+self.image_info["image_id"],self.image_info["x"],self.image_info["y"],self.image_info["name"],self.image_info["custom_frame"],self.image_info["image_path"])
					
			except Exception as e:
				
				
				output_file=self.image_info["image_path"]
				self.image_info["image_path"]="/usr/share/icons/Vibrancy-Colors/status/96/image-missing.png"
				image=Gtk.Image.new_from_file(self.image_info["image_path"])
					
				if self.image_info["video_url"] !=None:
					self.image_info["image_path"]="/usr/share/lliurex-store/lliurex-store-gui/rsrc/icons/clean_icons/video.svg"
				else:
					self.image_info["custom_frame"]=True
					self.image_info["force_label"]=True
				
				ret=ImageManager.create_banner(self.image_info["image_path"],self.image_info["x"],self.image_info["y"],self.image_info["name"],self.image_info["custom_frame"])
				self.image_info["pixbuf"]=ret[1].get_pixbuf()
				self.set_from_pixbuf(self.image_info)
				
		
		else:
			self.image_info["image_path"]=self.image_dir+self.image_info["image_id"]

		return True
		
	#def download-image-thread
	
	
	def create_banner_from_file(self,image_info,output_file=None):
		
		file_name=image_info.setdefault("image_path")
		x=image_info.setdefault("x")
		y=image_info.setdefault("y")
		custom_frame=image_info.setdefault("custom_frame",False)
		txt=image_info.setdefault("name",None)
		
		
		ret=ImageManager.create_banner(file_name,x,y,txt,custom_frame,output_file)
		
		if output_file ==None:
			image_info["pixbuf"]=ret[1].get_pixbuf()
			self.set_from_pixbuf(image_info)
		else:
			image_info["image_path"]=output_file
			self.set_from_file(image_info)
		
		
	#def create_banner_from_file
	
	
	def create_banner_from_url(self,image_info):
		
		self.set_image_info(self.image_info)
		self.download_image(image_info)
		
	#def create_banner_from_url
	
	
	def set_video_info(self,video_info):
		
		video_info.setdefault("video_url","")
		video_info.setdefault("image_url","")
		video_info.setdefault("image_id","")
		video_info.setdefault("x",-1)
		video_info.setdefault("y",-1)
		self.set_image_info(video_info)
		
		self.image_info["video_url"]=video_info.setdefault("video_url")
		self.image_info["image_url"]=video_info.setdefault("image_url")
		self.image_info["image_id"]=video_info.setdefault("image_id")
		self.image_info["x"]=video_info.setdefault("x")
		self.image_info["y"]=video_info.setdefault("y")
		self.image_info["package"]=video_info.setdefault("package","")
				
		self.download_image(video_info)
		
	#def set_video_info
	
	
#class ScreenshotNeo


if __name__=="__main__":
	
	w=Gtk.Window()
	w.connect("destroy",Gtk.main_quit)
	
	hbox=Gtk.HBox()
	vbox=Gtk.VBox()
	hbox.pack_start(vbox,False,False,0)
	w.add(hbox)
	
	s=ScreenshotNeo()
	info={}
	info["image_path"]="gearth2.png"
	info["x"]=300
	info["y"]=300
	info["aspect_ratio"]=True
	info["package"]="a"
	s.set_from_file(info)
	vbox.pack_start(Gtk.Label("load from file aspect_ratio=True"),False,False,0)
	vbox.pack_start(s,False,False,0)
	
	s=ScreenshotNeo()
	info={}
	info["image_path"]="gearth2.png"
	info["x"]=100
	info["y"]=100
	info["aspect_ratio"]=False
	info["package"]="a"
	s.set_from_file(info)
	vbox.pack_start(Gtk.Label("load from file aspect_ratio=False"),False,False,0)
	vbox.pack_start(s,False,False,0)
	
	s=ScreenshotNeo()
	info={}
	info["pixbuf"]=Gtk.Image.new_from_file("gearth3.png").get_pixbuf()
	info["aspect_ratio"]=True
	info["package"]="a"
	s.set_from_pixbuf(info)
	vbox.pack_start(Gtk.Label("load from pixbuf aspect_ratio=True"),False,False,0)
	vbox.pack_start(s,False,False,0)
	
	s=ScreenshotNeo()
	info={}
	info["pixbuf"]=Gtk.Image.new_from_file("gearth3.png").get_pixbuf()
	info["aspect_ratio"]=False
	info["package"]="a"
	info["x"]=100
	info["y"]=100
	s.set_from_pixbuf(info)
	vbox.pack_start(Gtk.Label("load from pixbuf aspect_ratio=False"),False,False,0)
	vbox.pack_start(s,False,False,0)
	
	s=ScreenshotNeo()
	info={}
	info["image_url"]="http://www.hdbloggers.net/wp-content/uploads/2016/10/Wallpaper-4K.jpg"
	info["image_id"]="wallpaper"
	info["aspect_ratio"]=True
	info["package"]="a"
	info["x"]=300
	info["y"]=300
	s.download_image(info)
	vbox.pack_start(Gtk.Label("url aspect_ratio=True"),False,False,0)
	vbox.pack_start(s,False,False,0)

	s=ScreenshotNeo()
	info={}
	info["image_url"]="http://no.existo.com/asd.jpg"
	info["image_id"]="wallpaper2"
	info["aspect_ratio"]=True
	info["package"]="Package name"
	info["x"]=128
	info["y"]=128
	s.download_image(info)
	vbox.pack_start(Gtk.Label("url 404 aspect_ratio=True"),False,False,0)
	vbox.pack_start(s,False,False,0)

	vbox1=Gtk.VBox()
	hbox.pack_start(vbox1,False,False,0)

	s=ScreenshotNeo()
	info={}
	info["image_path"]="/usr/share/pixmaps/firefox.png"
	info["image_id"]="firefox"
	info["aspect_ratio"]=True
	info["package"]="Firefox"
	info["custom_frame"]=True
	info["x"]=300
	info["y"]=300
	s.create_banner_from_file(info)
	vbox1.pack_start(Gtk.Label("create banner from file. resize_image=True"),False,False,0)
	vbox1.pack_start(s,False,False,0)

	s=ScreenshotNeo()
	info={}
	info["image_path"]="/home/cless/svn/xenial/lliurex-artwork-icons/trunk/fuentes/future-green/apps/scite.svg"
	info["image_id"]="scite"
	info["aspect_ratio"]=True
	info["package"]="SciTe"
	info["custom_frame"]=False
	info["x"]=200
	info["y"]=200
	s.create_banner_from_file(info)
	vbox1.pack_start(Gtk.Label("create banner from file. resize_image=False"),False,False,0)
	vbox1.pack_start(s,False,False,0)

	
	s=ScreenshotNeo()
	info={}
	info["image_url"]="http://androidportal.zoznam.sk/wp-content/uploads/2013/01/2013-purple-640x569.png"
	info["image_id"]="testing"
	info["aspect_ratio"]=True
	info["package"]="Custom banner"
	info["custom_frame"]=False
	info["force_label"]=True
	info["x"]=400
	info["y"]=400
	
	s.create_banner_from_url(info)
	vbox1.pack_start(Gtk.Label("create banner from URL. resize_image=False"),False,False,0)
	vbox1.pack_start(s,False,False,0)
	

	
	w.show_all()
	
	GObject.threads_init()
	Gtk.main()
	