import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio,GLib
import Screenshot
import ImageManager

import Core

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import time
import threading
from subprocess import Popen
import os
import html2text
import random
import copy

import gettext
gettext.textdomain('lliurex-store')
_ = gettext.gettext



class DetailsBox(Gtk.VBox):

	def __init__(self):
		
		Gtk.VBox.__init__(self)
		
		self.core=Core.Core.get_core()
		
		self.banner_full_size=250
		self.screenshot_small=100
		self.banner_small=135
		self.icon_size=64
		
		self.details_max_width=25
		self.app_max_width=8
		self.short_description_max_width=10
		
		self.full_info_box=Gtk.HBox()
		self.pack_start(self.full_info_box,True,True,5)
		
		self.related_aborted=False
		self.current_id=None
		
		# ####### LEFT SIDE ######
		
		self.app_details=Gtk.VBox()
		self.app_details.set_margin_left(10)
		self.app_details.set_margin_bottom(10)
		self.app_details.set_margin_top(5)
		self.full_info_box.pack_start(self.app_details,False,False,0)

		self.app_banner=Screenshot.ScreenshotNeo()
		self.app_banner.set_size_request(self.banner_full_size,self.banner_full_size)

		self.app_details.pack_start(self.app_banner,False,False,0)
		self.install_button=Gtk.Button()
		self.install_button_label=Gtk.Label(_("Install"))
		self.install_button.add(self.install_button_label)
		self.install_button.connect("clicked",self.install_clicked)
		
		vbox=Gtk.VBox()
		self.install_label=Gtk.Label(_("Installing..."))
		vbox.pack_start(self.install_label,False,False,0)
		vbox.set_valign(Gtk.Align.FILL)
		vbox.set_halign(Gtk.Align.FILL)
		
		self.install_label.set_halign(Gtk.Align.START)
		self.install_pbar=Gtk.ProgressBar()
		self.install_pbar.set_valign(Gtk.Align.FILL)
		self.install_pbar.set_halign(Gtk.Align.FILL)
		vbox.pack_start(self.install_pbar,True,True,0)

		hbox=Gtk.HBox()
		self.uninstall_button=Gtk.Button(_("Uninstall"))
		self.uninstall_button.connect("clicked",self.uninstall_clicked)
		self.open_button=Gtk.Button(_("Open"))
		self.open_button.connect("clicked",self.open_clicked)
		self.open_button.set_margin_right(10)
		hbox.pack_start(self.open_button,True,True,0)
		hbox.pack_start(self.uninstall_button,True,True,0)
		
		self.install_stack=Gtk.Stack()
		self.install_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
		self.install_stack.set_transition_duration(500)
		self.install_stack.add_titled(self.install_button,"install","Install")
		self.install_stack.add_titled(vbox,"progress","Progress")
		self.install_stack.add_titled(hbox,"installed","Open/Uninstall")
		
		self.app_details.pack_start(self.install_stack,False,False,10)
		
		self.details_label=Gtk.Label("Details")
		self.details_label.set_alignment(0,0.5)
		self.details_label.set_margin_left(0)
		self.app_details.pack_start(self.details_label,False,False,0)
		
		self.details_divider=Gtk.HBox()
		self.details_divider.set_size_request(0,1)
		self.app_details.pack_start(self.details_divider,False,False,5)
		
		self.version_label=Gtk.Label(_("Version"))
		self.version_label.set_alignment(0,0.5)
		self.category_label=Gtk.Label(_("Category"))
		self.category_label.set_alignment(0,0.5)
		self.license_label=Gtk.Label(_("License"))
		self.license_label.set_alignment(0,0.5)
		self.size_label=Gtk.Label(_("Size"))
		self.size_label.set_alignment(0,0.5)
		self.website_label=Gtk.Label(_("Website"))
		self.website_label.set_alignment(0,0.5)

		self.version_value_label=Gtk.Label()
		self.version_value_label.set_alignment(1,0.5)
		self.version_value_label.set_max_width_chars(self.details_max_width)
		self.version_value_label.set_ellipsize(Pango.EllipsizeMode.END)
		self.category_value_label=Gtk.Label()
		self.category_value_label.set_alignment(1,0.5)
		self.category_value_label.set_max_width_chars(self.details_max_width)
		self.category_value_label.set_ellipsize(Pango.EllipsizeMode.END)
		self.license_value_label=Gtk.Label()
		self.license_value_label.set_alignment(1,0.5)
		self.license_value_label.set_max_width_chars(self.details_max_width)
		self.license_value_label.set_ellipsize(Pango.EllipsizeMode.END)
		self.size_value_label=Gtk.Label()
		self.size_value_label.set_alignment(1,0.5)
		self.size_value_label.set_max_width_chars(self.details_max_width)
		self.size_value_label.set_ellipsize(Pango.EllipsizeMode.END)
		self.website_value_label=Gtk.Label()
		self.website_value_label.set_alignment(1,0.5)
		self.website_value_label.set_max_width_chars(self.details_max_width)
		self.website_value_label.set_ellipsize(Pango.EllipsizeMode.END)
		
		hbox=Gtk.HBox()
		hbox.pack_start(self.version_label,False,False,0)
		hbox.pack_end(self.version_value_label,False,False,0)
		self.app_details.pack_start(hbox,False,False,0)
		hbox=Gtk.HBox()
		hbox.pack_start(self.category_label,False,False,0)
		hbox.pack_end(self.category_value_label,False,False,0)
		self.app_details.pack_start(hbox,False,False,0)
		hbox=Gtk.HBox()
		hbox.pack_start(self.license_label,False,False,0)
		hbox.pack_end(self.license_value_label,False,False,0)
		self.app_details.pack_start(hbox,False,False,0)
		hbox=Gtk.HBox()
		hbox.pack_start(self.size_label,False,False,0)
		hbox.pack_end(self.size_value_label,False,False,0)
		self.app_details.pack_start(hbox,False,False,0)
		hbox=Gtk.HBox()
		hbox.pack_start(self.website_label,False,False,0)
		hbox.pack_end(self.website_value_label,False,False,0)
		self.app_details.pack_start(hbox,False,False,0)
		
		
		# ############# #
		
		# ####### RIGHT SIDE ######
		
		self.app_details_r=Gtk.VBox()
		self.app_details_r.set_margin_top(5)
		self.full_info_box.pack_start(self.app_details_r,True,True,20)
		
		hbox=Gtk.HBox()
		self.app_icon=Screenshot.ScreenshotNeo()
		self.app_icon.set_size_request(64,64)
		
		hbox.pack_start(self.app_icon,False,False,0)
		
		self.app_name_label=Gtk.Label("")
		self.app_name_label.set_max_width_chars(self.app_max_width)
		self.app_name_label.set_ellipsize(Pango.EllipsizeMode.END)
		self.app_name_label.set_alignment(0,1)
		self.short_description_label=Gtk.Label("")
		self.short_description_label.set_alignment(0,0)
		self.short_description_label.set_max_width_chars(self.short_description_max_width)
		self.short_description_label.set_ellipsize(Pango.EllipsizeMode.END)
		
		vbox=Gtk.VBox()
		vbox.pack_start(self.app_name_label,True,True,0)
		vbox.pack_start(self.short_description_label,True,True,0)
		hbox.pack_start(vbox,True,True,5)
		
		self.app_details_r.pack_start(hbox,False,False,0)
		
		self.full_description_label=Gtk.Label()
		self.full_description_label.set_margin_right(10)
		self.full_description_label.set_alignment(0,1)
		self.full_description_label.set_justify(Gtk.Justification.FILL)
		self.full_description_label.set_line_wrap(True)
		self.full_description_label.set_valign(Gtk.Align.START)
		self.full_description_label.set_halign(Gtk.Align.FILL)
		
		sw=Gtk.ScrolledWindow()
		sw.set_shadow_type(Gtk.ShadowType.NONE)
		sw.set_overlay_scrolling(True)
		sw.set_kinetic_scrolling(True)
		vp=Gtk.Viewport()
		sw.add(vp)
		sw.set_size_request(0,100)
		vp.add(self.full_description_label)
		
		self.app_details_r.pack_start(sw,True,True,10)
		
		self.description_divider=Gtk.HBox()
		self.description_divider.set_size_request(0,1)
		self.description_divider.set_valign(Gtk.Align.START)
		self.app_details_r.pack_start(self.description_divider,False,False,5)
		
		ss_sw=Gtk.ScrolledWindow()
		ss_sw.set_shadow_type(Gtk.ShadowType.NONE)
		ss_vp=Gtk.Viewport()
		
		ss_sw.add(ss_vp)
		
		self.screenshots_box=Gtk.HBox()
		
		ss_sw.set_size_request(0,130)
		vbox=Gtk.VBox()
		vbox.pack_start(self.screenshots_box,True,False,0)
		ss_vp.add(vbox)
		self.app_details_r.set_valign(Gtk.Align.FILL)
		self.app_details_r.pack_start(ss_sw,False,False,5)
		
		
		# ####################### #
		
		# ## RELATED #######
		
		related_vbox=Gtk.VBox()
		related_vbox.set_margin_left(10)
		
		self.related_label=Gtk.Label(_("Related"))
		self.related_label.set_alignment(0,1)
		
		related_vbox.pack_start(self.related_label,False,False,0)
				
		self.related_divider=Gtk.HBox()
		self.related_divider.set_size_request(0,1)
		self.related_divider.set_margin_right(20)
		related_vbox.pack_start(self.related_divider,False,False,5)
		
		self.related_sw=Gtk.ScrolledWindow()
		self.related_sw.set_shadow_type(Gtk.ShadowType.NONE)
		self.related_sw.set_size_request(0,self.banner_small+40)
		self.related_sw.set_margin_right(20)
		related_vp=Gtk.Viewport()
		self.related_sw.add(related_vp)
		
		self.related_box=Gtk.HBox()
		self.related_box.set_margin_bottom(10)
		
		related_vp.add(self.related_box)
		related_vp.connect('scroll-event', self.on_hscroll)
		
		related_vbox.pack_start(self.related_sw,False,False,5)
		self.pack_start(related_vbox,True,True,0)
		
		# #################

		self.set_css_info()
		
	#def  init
	
	def on_hscroll(self, widget, event):
		adj=widget.get_hadjustment()
		if event.get_scroll_deltas()[2]>0:
			adj.set_value(adj.get_value()+10)
		else:
			adj.set_value(adj.get_value()-10)
	#def on_hscroll

	def set_package_info(self,pkg):
		
		self.current_id=random.random()
		
		info={}
		
		info["image_url"]=pkg["banner_small"]
		info["image_id"]=pkg["package"]+"_banner_small"
		info["x"]=self.banner_full_size
		info["y"]=self.banner_full_size
		info["aspect_ratio"]=False
		info["name"]=pkg["package"].capitalize()
		info["installed"]=True if pkg["state"]=="installed" else False
		
		if pkg["banner_small"] !=None:
			self.app_banner.download_image(info)
		else:
			info["name"]=None
			if os.path.exists(self.core.tmp_store_dir+info["image_id"]):
				
				info["image_path"]=self.core.tmp_store_dir+info["image_id"]
				self.app_banner.set_from_file(info)
			else:
				info["image_path"]=self.core.resources.get_icon(pkg)
			
				self.app_banner.create_banner_from_file(info)
		
		self.version_value_label.set_text(pkg["version"])
		self.category_value_label.set_text(pkg["category"])
		self.license_value_label.set_text(pkg["license"])
		try:
			size= "{:.2f} MB".format(float(pkg["size"])/1000000) 
			self.size_value_label.set_text(size)
		except:
			pass
		self.website_value_label.set_markup("<a href=\"%s\">%s</a>"%(pkg["homepage"],pkg["homepage"]))
		self.app_name_label.set_text(pkg["name"])
		self.short_description_label.set_text(pkg["summary"])
		h=html2text.HTML2Text()
		h.body_width=500
		txt=h.handle(pkg["description"])
		txt=txt.replace("&lt;", "<")
		txt=txt.replace("&gt;", ">")
		txt=txt.replace("&amp;", "&")
		self.full_description_label.set_text(txt)
		
		if info["installed"]:
			self.install_stack.set_visible_child_name("installed")
		else:
			self.install_stack.set_visible_child_name("install")
			
		
		info["image_path"]=self.core.resources.get_icon(pkg)
		info["image_id"]=pkg["icon"]+"_icon"
		info["x"]=self.icon_size
		info["y"]=self.icon_size
		
		self.app_icon.set_from_file(info)
		
		for s in self.screenshots_box.get_children():
			self.screenshots_box.remove(s)
		
		count=0
		for v in pkg["videos"]:
			
			image=Screenshot.ScreenshotNeo()
			info["video_url"]=v["url"].replace("http://metadata.tanglu.org/appstream/media/xenial/","").replace("https://www.youtube.com/watch?v=","https://www.youtube.com/embed/")
			info["image_url"]=v["preview"]
			info["image_id"]=pkg["package"]+"_video_"+str(count)
			info["x"]=self.screenshot_small
			info["y"]=self.screenshot_small
			
			image.set_video_info(info)
			
			b=Gtk.Button()
			b.set_name("RELATED_BUTTON")
			b.add(image)
			self.screenshots_box.pack_start(b,False,False,5)
			
			count+=1
			
		count=0
		for s in pkg["screenshots"]:
			
			image=Screenshot.ScreenshotNeo()
			i={}
			
			i["image_url"]=s
			i["image_id"]=pkg["package"]+"_screenshot_"+str(count)
			i["x"]=self.screenshot_small
			i["y"]=self.screenshot_small
			i["aspect_ratio"]=False
						
			image.download_image(i)
			b=Gtk.Button()
			b.set_name("RELATED_BUTTON")
			b.add(image)
			self.screenshots_box.pack_start(b,False,False,5)
			count+=1
		
		self.screenshots_box.show_all()

		for p in self.related_box.get_children():
			self.related_box.remove(p)
		
		categories=copy.deepcopy(pkg["categories"])
		
		self.related=None
		
		self.related_thread=threading.Thread(target=self.search_related_packages_from_categories_thread,args=(pkg["package"],categories,self.current_id))
		self.related_thread.daemon=True
		self.related_thread.start()
		GLib.timeout_add(500,self.related_pkg_listener,self.current_id)
		
		'''
		for p in pkg["related_packages"]:
			
			image=Screenshot.ScreenshotNeo()

			i={}
			i["image_id"]=p["package"]+"_banner_small"
			i["x"]=self.banner_small
			i["y"]=self.banner_small
			i["name"]=p["package"].capitalize()
			i["package"]=p["package"]
			i["icon"]=p["icon"]
			i["component"]=p["component"]

			if p["banner"]!=None:
				i["image_url"]=p["banner"]
				i["custom_frame"]=False
			else:
				i["image_path"]=self.core.resources.get_icon(p)
				i["custom_frame"]=True
				
			if not i["custom_frame"]:
				image.download_image(i)
			else:
				i["force_text"]=True
				image.create_banner_from_file(i)
			
			b=Gtk.Button()
			b.add(image)
			b.set_size_request(self.banner_small,self.banner_small)
			b.set_margin_top(10)
			b.connect("clicked",self.related_app_clicked,p)
			b.set_name("RELATED_BUTTON")
			b.set_valign(Gtk.Align.CENTER)
			b.set_tooltip_text(p["name"])
			self.related_box.pack_start(b,False,False,3)
		
		self.related_sw.get_hadjustment().set_value(0)
		self.related_box.show_all()
		'''
		
		for x in self.screenshots_box.get_children():
			x.connect("clicked",self.core.main_window.screenshot_clicked)
		
		
	#def set_values
	
	
	def search_related_packages_from_categories_thread(self,pkg,categories,id):

		self.related=self.core.store.get_random_packages_from_categories(pkg,categories)
		
	#def search_related_packages_from_categories_thread
	
	def related_pkg_listener(self,id):
		
		if id!=self.current_id:
			return False
			
		if self.related_thread.is_alive():
			return True
			
		if self.related!=None:
			
			
			for p in self.related["related_packages"]:
				
				image=Screenshot.ScreenshotNeo()

				i={}
				i["image_id"]=p["package"]+"_banner_small"
				i["x"]=self.banner_small
				i["y"]=self.banner_small
				i["name"]=p["package"].capitalize()
				i["package"]=p["package"]
				i["icon"]=p["icon"]
				i["component"]=p["component"]

				if p["banner"]!=None:
					i["image_url"]=p["banner"]
					i["custom_frame"]=False
				else:
					i["image_path"]=self.core.resources.get_icon(p)
					i["custom_frame"]=True
					
				if not i["custom_frame"]:
					image.download_image(i)
				else:
					i["force_text"]=True
					image.create_banner_from_file(i)
				
				b=Gtk.Button()
				b.add(image)
				b.set_size_request(self.banner_small,self.banner_small)
				b.set_margin_top(10)
				b.connect("clicked",self.related_app_clicked,p)
				b.set_name("RELATED_BUTTON")
				b.set_valign(Gtk.Align.CENTER)
				b.set_tooltip_text(p["name"])
				self.related_box.pack_start(b,False,False,3)
			
			self.related_sw.get_hadjustment().set_value(0)
			self.related_box.show_all()			
			
			
		return False
			
	#def related_pkg_listener
	
	
	def set_css_info(self):
		
		self.style_provider=Gtk.CssProvider()
		f=Gio.File.new_for_path(self.core.rsrc_dir+"lliurex-store.css")
		self.style_provider.load_from_file(f)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
		self.set_name("DETAILS_BOX")
		
		self.details_divider.set_name("DIVIDER")
		self.description_divider.set_name("DIVIDER")
		self.related_divider.set_name("DIVIDER")
		
		self.details_label.set_name("DETAILS_LABEL")
		self.version_label.set_name("DETAILS_OPTIONS")
		self.category_label.set_name("DETAILS_OPTIONS")
		self.license_label.set_name("DETAILS_OPTIONS")
		self.size_label.set_name("DETAILS_OPTIONS")
		self.website_label.set_name("DETAILS_OPTIONS")
		
		self.version_value_label.set_name("DETAILS_VALUES")
		self.category_value_label.set_name("DETAILS_VALUES")
		self.license_value_label.set_name("DETAILS_VALUES")
		self.size_value_label.set_name("DETAILS_VALUES")
		self.website_value_label.set_name("DETAILS_VALUES")
		
		self.app_name_label.set_name("TITLE")
		self.short_description_label.set_name("SHORT_DESCRIPTION")
		self.full_description_label.set_name("FULL_DESCRIPTION")
		
		self.related_label.set_name("RELATED_LABEL")
		
		self.install_button.set_name("INSTALL_BUTTON")
		self.install_label.set_name("DETAILS_LABEL")
		self.uninstall_button.set_name("UNINSTALL_BUTTON")
		self.open_button.set_name("INSTALL_BUTTON")
		
	#def set-css_info
	
	
	def related_app_clicked(self,widget,app):
		
		self.core.main_window.load_pkg_data(app["package"])
		
	#def related_app_clicked
	
	
	def install_clicked(self,widget):
		
		self.install_label.set_text("Installing...")
		self.install_stack.set_visible_child_name("progress")
		
		t=threading.Thread(target=self.install_pkg)
		t.daemon=True
		t.start()
		GLib.timeout_add(100,self.pulse_pbar,t,"installed","install")
		
	#def install_clicked
	
	
	def uninstall_clicked(self,widget):
		
		self.install_label.set_text("Uninstalling...")
		self.install_stack.set_visible_child_name("progress")
		
		t=threading.Thread(target=self.uninstall_pkg)
		t.daemon=True
		t.start()
		GLib.timeout_add(100,self.pulse_pbar,t,"install","installed")
		
	#def install_clicked
	
		
	def pulse_pbar(self,t,target,fallback):
		
		if t.is_alive():
			self.install_pbar.pulse()
			return True
		
		
		if self.thread_ret:
			self.install_stack.set_visible_child_name(target)
		else:
			self.install_stack.set_visible_child_name(fallback)
		
		return False
		
	#def pulse_pbar
	
	
	def install_pkg(self):
		
		pkg=self.core.main_window.current_pkg["package"]
		self.thread_ret=self.core.store.install_package(pkg)
		
	#def install_pkg
	
	
	def uninstall_pkg(self):
		
		pkg=self.core.main_window.current_pkg["package"]
		self.thread_ret=self.core.store.uninstall_package(pkg)
		
	#def uninstall_pkg
	
	
	def open_clicked(self,widget):
		if self.core.main_window.current_pkg["name"].endswith('.snap'):
			snap=self.core.main_window.current_pkg["bundle"]["snap"].replace('.snap','')
			Popen(["snap","run","{}".format(snap)])
		elif self.core.main_window.current_pkg["package"].endswith('.appimage'):
			appimg=self.core.main_window.current_pkg["package"].lower()
			if os.path.exists(os.getenv("HOME")+"/.local/bin/%s"%appimg):
				Popen([os.getenv("HOME")+"/.local/bin/%s"%appimg])
			elif os.path.exists(os.getenv("HOME")+"/Applications/%s"%appimg):
				Popen([os.getenv("HOME")+"/Applications/%s"%appimg])
		elif "zomando" in self.core.main_window.current_pkg["name"]:
			zmd=self.core.main_window.current_pkg["name"].replace('.zomando','.zmd')
			zmd=os.path.join("/usr/share/zero-center/zmds",zmd)
			cmd=[zmd]
			if os.path.exists(zmd):
				pkexec=False
				app=zmd.replace(".zmd",".app")
				app=app.replace("zmds","applications")
				if os.path.exists(app):
					with open(app,'r') as f:
						for l in f.readlines():
							if "pkexec" in l:
								pkexec=True
								break
				if pkexec:
					cmd.insert(0,"pkexec")
				Popen(cmd)
		elif "flatpak" in self.core.main_window.current_pkg["name"]:
			Popen(["flatpak","run","%s"%self.core.main_window.current_pkg["id"]])
		else:
			desktop="{}.desktop".format(self.core.main_window.current_pkg["pkgname"])
			deskPath=os.path.join("/usr/share/applications/",desktop)
			idPath=os.path.join("/usr/share/applications/",self.core.main_window.current_pkg["id"])
			if os.path.isfile(deskPath):
				os.system("gtk-launch %s"%desktop)
			elif os.path.exists(idPath):
				os.system("gtk-launch %s"%self.core.main_window.current_pkg["id"])
		
	#def open_clicked
	
