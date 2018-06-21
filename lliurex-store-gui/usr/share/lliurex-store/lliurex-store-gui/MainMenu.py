import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio, GObject,GLib

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import urllib.request as urllib2
import shutil
import json
import random

import Core
import Screenshot
import ImageManager
import Package
import os

import gettext
gettext.textdomain('lliurex-store')
_ = gettext.gettext


HOME_CONTENT_URL="http://svn.lliurex.net/xenial/lliurex-store/trunk/fuentes/lliurex-store-gui/usr/share/lliurex-store/lliurex-store-gui/rsrc/home_content.json"
HOME_CONTENT_URL="file:///usr/share/lliurex-store/lliurex-store-gui/rsrc/home_content.json.new"


class MainMenu(Gtk.VBox):
	
	def __init__(self):
		
		Gtk.VBox.__init__(self)
		
		self.paused=False
		self.max_image_id=5
		
		self.banner_large_x=735
		self.banner_large_y=180
		self.banner_small=134
		
		self.core=Core.Core.get_core()
		
		ui_path=self.core.ui_path
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-store')
		builder.add_from_file(ui_path)
		
		self.main_view_box=builder.get_object("main_view_box")
		self.divider1=builder.get_object("mv_divider1")
		self.divider2=builder.get_object("mv_divider2")
		self.divider3=builder.get_object("mv_divider3")
		self.featured_label=builder.get_object("featured_label")
		self.categories_label=builder.get_object("categories_label")
		self.featured_extra_box=builder.get_object("featured_extra_box")
		self.rewind_button=builder.get_object("media_rewind_button")
		self.play_button=builder.get_object("media_play_button")
		self.forward_button=builder.get_object("media_forward_button")
		self.media_play_image=builder.get_object("media_play_image")
		self.categories_grid=builder.get_object("categories_grid")

		self.image_stack=Gtk.Stack()
		self.image_stack.set_transition_duration(800)
		self.image_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.image_stack.set_margin_right(10)
		self.image_stack.set_margin_left(10)
		self.image_stack.set_size_request(self.banner_large_x,self.banner_large_y)
		self.image_stack.set_halign(Gtk.Align.CENTER)
		
		self.main_view_box.pack_start(self.image_stack,False,False,10)
		self.main_view_box.reorder_child(self.image_stack,2)
		
		'''
		
		# MIGHT OR MIGHT NOT DO THIS IN THE FUTURE
		
		self.categories_flowbox = Gtk.FlowBox()
		self.categories_flowbox.set_max_children_per_line(30)
		self.categories_flowbox.set_column_spacing(0)
		self.categories_flowbox.set_row_spacing(0)
		self.categories_flowbox.set_margin_left(10)
		self.categories_flowbox.set_margin_right(10)
		self.categories_flowbox.set_halign(Gtk.Align.FILL)
		
		self.main_view_box.pack_start(self.categories_flowbox,False,False,10)
		'''
		
		self.pack_start(self.main_view_box,True,True,0)
		
		self.rewind_button.connect("clicked",self.rewind_clicked)
		self.play_button.connect("clicked",self.play_clicked)
		self.forward_button.connect("clicked",self.forward_clicked)
		
		self.build_categories()
		self.set_css_names()
		
		GLib.timeout_add(5000,self.next_image)
		
	#def __init__
	
	def download_home_info(self):
		
		#HOME_CONTENT_URL
		
		header = {
					'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
				}
			
		try:
			
			self.core.dprint("Downloading home_content.json...")
			
			
			req=urllib2.Request(HOME_CONTENT_URL,headers=header)
			res=urllib2.urlopen(req)
			
			f=open(self.core.tmp_store_dir+"home_content.json","w")
			f.write(res.read().decode("utf-8"))
			f.close()
			
			
			f=open(self.core.tmp_store_dir+"home_content.json")
			self.home_info=json.load(f)
			
			f.close()

		except Exception as e:
			
			print(e)
		
		
	#def download_home_info
	
	def build_banners(self):

		# Main banners
		
		spacing=5
		count=1
		self.max_image_id=len(self.home_info["large"])
		for pkg in self.home_info["large"]:
			s=Screenshot.ScreenshotNeo()
			info={}
			info["image_url"]=pkg["banner_large"]
			info["image_id"]=pkg["package"]+"_banner_large"
			info["x"]=self.banner_large_x
			info["y"]=self.banner_large_y
			info["aspect_ratio"]=True
			info["name"]=pkg["name"]
			info["package"]=pkg["package"]
			s.download_image(info)
			s.set_size_request(self.banner_large_x,self.banner_large_y)
			b=Gtk.Button()
			b.set_name("RELATED_BUTTON")
			b.add(s)
			b.show_all()
			b.set_size_request(self.banner_large_x,self.banner_large_y)
			b.connect("clicked",self.banner_clicked,pkg)
			self.image_stack.add_titled(b,"image%s"%count,"Image %s"%count)
			count+=1

		
		# Smaller banners
		
		
		banner_range=range(0,len(self.home_info["small"]))
		sample=random.sample(banner_range,5)
		
		for b_id in banner_range:
			
			pkg=self.home_info["small"][b_id]
			s=Screenshot.ScreenshotNeo()
			info={}
			if pkg["banner_small"]!=None:
				info["image_url"]=pkg["banner_small"]
				info["aspect_ratio"]=False
			else:
				info["image_path"]=self.core.resources.get_icon(pkg)
				info["aspect_ratio"]=True
				info["custom_frame"]=True
				
			info["image_id"]=pkg["package"]+"_banner_small"
			info["x"]=self.banner_small
			info["y"]=self.banner_small
			info["name"]=pkg["name"]
			info["package"]=pkg["package"]
			
			if pkg["banner_small"]!=None:
				s.download_image(info)
			else:
				s.create_banner_from_file(info)
			b=Gtk.Button()
			b.set_name("RELATED_BUTTON")
			b.add(s)
			b.connect("clicked",self.banner_clicked,pkg)
			self.featured_extra_box.pack_start(b,True,False,spacing)
				
		
		self.show_all()
		
	#def build_related
	
	
	def build_categories(self):
		
		max_width=7
		w_counter=0
		h_counter=0
		button_size=97
		
				
		for item in sorted(self.core.categories_manager.categories):
			
			icon_name=self.core.categories_manager.categories[item]["icon"]
			label=_(item)
		
			b=Gtk.Button()
			b.set_name("RELATED_BUTTON")
			hbox=Gtk.HBox()
			hbox.set_halign(Gtk.Align.START)
						
			s=Screenshot.ScreenshotNeo()
			i={}
			i["image_path"]=icon_name
			i["x"]=button_size
			i["y"]=button_size
			i["custom_frame"]=True
			i["name"]=label
			s.create_banner_from_file(i)
			b.add(s)
			b.connect("clicked",self.category_clicked,item)

			'''
			self.categories_flowbox.add(b)
			'''
			self.categories_grid.attach(b,w_counter,h_counter,1,1)
			w_counter+=1
			if w_counter ==max_width:
				w_counter=0
				h_counter+=1
			
		self.categories_grid.show_all()
		
		'''
		self.categories_flowbox.show_all()
		'''
		
	#def build_categories
	
	
	def set_css_names(self):
		
		self.main_view_box.set_name("DETAILS_BOX")
		self.divider1.set_name("DIVIDER")
		self.divider2.set_name("DIVIDER")
		self.divider3.set_name("DIVIDER")
		self.featured_label.set_name("RELATED_LABEL")
		self.categories_label.set_name("RELATED_LABEL")
		self.rewind_button.set_name("MEDIA_BUTTON")
		self.play_button.set_name("MEDIA_BUTTON")
		self.forward_button.set_name("MEDIA_BUTTON")
		
	#def set_css_info
	
	
	def banner_clicked(self,widget,pkg):
		
		p=Package.Package(pkg)
		self.core.main_window.load_pkg_data(p["package"])
		
	#def banner_clicked

	
	def category_clicked(self,widget,category_tag):
		
		self.core.search_box.current_category=_(category_tag)
		self.core.main_window.search_category(category_tag)
		
	#def category_clicked
	
	
	def next_image(self,force=False,add=True):
		
		tmp=self.image_stack.get_visible_child_name()
		if tmp!=None:
			id=int(tmp.split("image")[1])
			
			if add:
			
				if id < self.max_image_id:
					id+=1
				else:
					id=1
			else:
				
				if id <= 1:
					id=self.max_image_id
				else:
					id-=1
			
			id="image%s"%id
			
			if not self.paused or force:
				if not self.image_stack.get_transition_running() or force:
					self.image_stack.set_visible_child_name(id)
			
		return True
		
	#def next_image

	
	def rewind_clicked(self,widget):
		
		self.image_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.next_image(True,False)
		self.image_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		
	#def rewind_clicked

	
	def play_clicked(self,widget):

		if self.paused:
			self.media_play_image.set_from_file(self.core.rsrc_dir + "icons/media/media_pause.svg")
		else:
			self.media_play_image.set_from_file(self.core.rsrc_dir+ "icons/media/media_play.svg")
			
		self.paused=not self.paused
		
	#def rewind_clicked

	
	def forward_clicked(self,widget):
		
		self.next_image(True)
		
	#def rewind_clicked
	
#class MainMenu
