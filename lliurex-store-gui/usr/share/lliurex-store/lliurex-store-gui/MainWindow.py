import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio, GObject,GLib

import Core
import Package

import threading
import multiprocessing
import time
import copy

import gettext
gettext.textdomain('lliurex-store')
_ = gettext.gettext

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


class MainWindow:
	
	def __init__(self):
		
		self.core=Core.Core.get_core()
		self.load_thread=threading.Thread()
		self.search_process=multiprocessing.Process()
		self.thread_aborted=False
		self.search_aborted=False
		self.last_search=""
		self.path_followed=["main"]
		self.load_gui()
		
	#def init
	
	
	# ### MAIN UI FUNCTIONS # ####################
	
	def load_gui(self):
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-store')
		ui_path=self.core.ui_path
		builder.add_from_file(ui_path)
		
		self.window=builder.get_object("window1")
		self.menu_button=builder.get_object("menu_button")
		
		self.main_scroll=builder.get_object("main_scrolledwindow")
		self.location_label=builder.get_object("location_label")
		self.search_entry=builder.get_object("search_entry")
		self.main_box=builder.get_object("main_box")
		self.header_box=builder.get_object("header_box")
		self.go_back_button=builder.get_object("go_back_button")
		
		
		
		self.main_menu=self.core.main_menu
		self.loading_box=self.core.loading_box
		self.details_box=self.core.details_box
		self.popup_menu=self.core.popup_menu
		self.screenshot_viewer=self.core.screenshot_viewer
		self.search_box=self.core.search_box
		
		self.stack=Gtk.Stack()
		self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
		self.stack.set_transition_duration(500)
		
		self.stack.add_titled(self.loading_box,"loading","Loading")
		self.stack.add_titled(self.main_menu,"main","Main")
		self.stack.add_titled(self.details_box,"details","Details")
		self.stack.add_titled(self.search_box,"search","Search")
		self.main_scroll.add(self.stack)
	
		self.overlay=Gtk.Overlay()
		self.main_eb=Gtk.EventBox()
		self.main_eb.add(self.main_box)
		
		self.main_eb.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
		self.main_eb.connect("button-press-event",self.main_eb_clicked)
		
		self.overlay.add(self.main_eb)
		self.overlay.show_all()
		
		self.fade_box_revealer=Gtk.Revealer()
		self.fade_box_revealer.set_valign(Gtk.Align.END)
		self.fade_box_revealer.set_halign(Gtk.Align.END)
		
		self.fade_box=Gtk.HBox()
		self.fade_eb=Gtk.EventBox()
		self.fade_eb.add(self.fade_box)
		self.fade_eb.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
		self.fade_eb.connect("button-press-event",self.main_eb_clicked)
		
		self.fade_box_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
		self.fade_box_revealer.set_transition_duration(self.popup_menu.revealer.get_transition_duration())
		self.fade_box_revealer.add(self.fade_eb)
		self.fade_box_revealer.show_all()
		
		
		self.overlay.add_overlay(self.fade_box_revealer)
		self.overlay.add_overlay(self.popup_menu)
		self.overlay.add_overlay(self.screenshot_viewer)

		self.window.add(self.overlay)
		
		self.connect_signals()
		self.set_css_info()
		self.build_home()
		
		self.window.show_all()
		
	#def load_gui

	
	def set_css_info(self):
		
		self.style_provider=Gtk.CssProvider()
		f=Gio.File.new_for_path(self.core.rsrc_dir+"lliurex-store.css")
		self.style_provider.load_from_file(f)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
		self.window.set_name("MAIN_BOX")
		self.header_box.set_name("HEADER_MENU")
		self.menu_button.set_name("MENU_BUTTON")
		self.location_label.set_name("RELATED_LABEL")
		self.fade_box.set_name("FADE_BOX")
		self.go_back_button.set_name("BACK_BUTTON")
		
	#def set-css_info	

	
	def connect_signals(self):
		
		self.window.connect("size-allocate",self.window_size_changed)
		self.window.connect("destroy",Gtk.main_quit)
		self.menu_button.connect("clicked",self.menu_button_clicked)
		self.search_entry.connect("changed",self.search_entry_changed)
		self.search_entry.connect("activate",self.entries_press_event)
		self.go_back_button.connect("clicked",self.go_back)
		
	#def connect_signals
	
	
	def start_gui(self):
		
		GObject.threads_init()
		Gtk.main()
		
	#def start_gui

	# #################################################### ##



	# #### STACK FAST ACCESS FUNCTIONS # #################
	
	def go_back(self,widget=None):
		
		if len(self.path_followed)>1:
			
			
			current_txt=self.location_label.get_text().split(" > ")
			current_txt=" > ".join(current_txt[0:-1])
			self.location_label.set_text(current_txt)
			dest=self.path_followed[-2]
			self.stack.set_visible_child_name(dest)
			self.path_followed.pop(-1)
			self.main_scroll.get_vadjustment().set_value(0)
			self.core.search_box.search_sw.get_vadjustment().set_value(0)
			
			if dest=="main":
				self.search_entry.set_text("")
		
	#def go_back
	
	
	def show_loading(self):
		
		self.stack.set_visible_child_name("loading")
		
	#def show_loading


	def show_details_box(self):
		
		self.thread_aborted=True
		self.search_aborted=True
		current_txt=self.location_label.get_text()
		if self.path_followed[-1]!="details":
			self.location_label.set_text(current_txt + " > " + _("Details"))
			self.path_followed.append("details")
		self.stack.set_visible_child_name("details")
		
	#def show_details_box


	def show_home(self):
		
		self.thread_aborted=True
		self.search_aborted=True
		
		self.search_entry.set_text("")
		self.location_label.set_text(_("Home"))
		self.path_followed=["main"]
		self.stack.set_visible_child_name("main")
		
	#def show_details_box
	
	
	def show_search_results(self,category=None):
		
		current_txt=self.location_label.get_text()
		
		if category==None:
			category=_("Search")
		
		if self.path_followed[-1]=="details":
			self.path_followed.pop(-1)
			current_txt=" > ".join(current_txt.split(" > ")[0:-1])
		
		if self.path_followed[-1]=="search":
			current_txt="".join(current_txt.split(" > ")[0:-1])
		else:
			self.path_followed.append("search")
			
		self.location_label.set_text(current_txt + " > " + category)
		self.stack.set_visible_child_name("search")
		
	#def show_search_results
	
	# ############################################



	# ### HOME LOADING FUNCTIONS # ##############
	
	def build_home(self):
		
		self.load_thread=threading.Thread(target=self.download_home_info_thread)
		self.load_thread.daemon=True
		self.load_thread.start()
		
		GLib.timeout_add(500,self.build_home_listener)
		self.window.set_title(_("LliureX Store - Wait while loading apps"))
		self.screenshot_viewer.set_sensitive(False)
		self.screenshot_viewer.revealer.set_reveal_child(True)
		GLib.timeout_add(1000,self.get_load_status)
		
	#def build_home


	def build_home_listener(self):
		
		if self.thread_aborted:
			self.thread_aborted=False
			return False
		
		
		if self.load_thread.is_alive():
			return True
		
		self.main_menu.build_banners()
		self.show_home()
		return False
		
	#def load_home

	
	def download_home_info_thread(self):
		
		self.main_menu.download_home_info()

	#def load_home_thread
	
	# #################################

	
	
	# ### LOAD PKG FUNCTIONS # ##################
	
	
	def set_pkg_data(self,pkg):
		
		self.current_pkg=Package.Package(pkg)
		self.details_box.set_package_info(self.current_pkg)
		self.show_details_box()
		
	#def set_data
	
	
	def load_pkg_data(self,pkg_id,pkg_data=None):
		
		self.current_pkg=None
		self.thread_aborted=False
		self.load_thread=threading.Thread(target=self.load_pkg_data_thread,args=(pkg_id,))
		self.load_thread.daemon=True
		self.load_thread.start()
		self.show_loading()
		GLib.timeout_add(500,self.load_pkg_listener)
		
	#def load_pkg_data
	
	
	def load_pkg_data_thread(self,pkg_id):
		
		self.current_pkg=self.core.store.get_info(pkg_id)
			
	#def load_pkg_data_thread
	
	
	def load_pkg_listener(self):
		
		if self.thread_aborted:
			self.thread_aborted=False
			return False
		
		if self.load_thread.is_alive():
			return True
			
		if self.current_pkg!=None:
			self.details_box.set_package_info(self.current_pkg)
			self.show_details_box()
		else:
			self.show_home()
		return False
		
	#def load_pkg_listener
	
	# #################################


	# ## SEARCH FUNCTIONS ######################
	
	
	def entries_press_event(self,widget):
		
		self.last_search=None
		self.search_entry_changed(None)
		
	#def entries_press_event
	
	
	def search_entry_changed(self,widget):
		
		txt=self.search_entry.get_text()
		current_stack=self.stack.get_visible_child_name()
		txt=txt.strip(" ")
		
		if self.last_search!=txt:
			self.last_search=txt
		else:
			return
		
		if len(txt)==0:
			self.show_home()
			return
			
		if len(txt)>2:
			self.search_aborted=False
			self.show_loading()
			self.search_package(txt)
		
	#def search_entry_changed
	
	
	def search_package(self,pkg_id):
		
		if self.search_process.is_alive():
			self.search_process.terminate()
		
		self.current_search_id=self.core.get_random_id()
		self.counter=0
		self.search_queue=multiprocessing.Queue()
		self.search_process=multiprocessing.Process(target=self.search_package_thread,args=(pkg_id,self.search_queue,))
		
		self.search_process.daemon=True
		self.search_process.start()
		
		GLib.timeout_add(500, self.search_listener,self.current_search_id)
		
	#def search_package
	
	
	def search_package_thread(self,pkg_id,search_queue):
		
		ret=self.core.store.search_package(pkg_id)
		self.core.dprint("Search complete")
		search_queue.put(ret)
		
	#def search_package_thread
	
	
	def search_listener(self,search_id):
		
		if self.current_search_id!=search_id:
			return False
		
		if self.search_aborted:
			self.core.dprint("Search aborted [!]")
			self.thread_aborted=False
			return False
		
		if self.search_process.is_alive():
			self.counter+=1
			
			if self.search_queue.empty():
				return True
			
		search_result=self.search_queue.get()
		
		if search_result!=None:
			self.core.search_box.populate_search_results(search_result)
			self.show_search_results()
		
		return False
		
	#def search_listener
	

	# ########################################
	
	# ### SEARCH CATEGORIES #### #
	
	def search_category(self,category):
	
		if self.search_process.is_alive():
			self.search_process.terminate()
	

		self.search_aborted=False
		self.show_loading()
		
		self.current_search_id=self.core.get_random_id()
		self.counter=0
		self.search_queue=multiprocessing.Queue()
		self.search_process=multiprocessing.Process(target=self.search_category_thread,args=(category,self.search_queue,))
		
		self.search_process.daemon=True
		self.search_process.start()
		
		GLib.timeout_add(500, self.search_category_listener,self.current_search_id)
	
	#def search_category
	
	
	def search_category_thread(self,category,search_queue):
		
		ret=self.core.store.get_package_list_from_category(category)
		self.core.dprint("Search complete")
		search_queue.put(ret)
		
	#def search_package_thread
	
	
	def search_category_listener(self,search_id):
		
		if self.current_search_id!=search_id:
			return False
		
		if self.search_aborted:
			self.core.dprint("Search aborted [!]")
			self.thread_aborted=False
			return False
		
		if self.search_process.is_alive():
			self.counter+=1
			
			if self.search_queue.empty():
				return True
			
		search_result=self.search_queue.get()
		
		if search_result!=None:
			
			search_result,categories=search_result
			self.core.search_box.populate_search_results(search_result,categories)
			self.show_search_results(self.core.search_box.current_category)
		
		return False
		
	#def search_listener
	
	
	
	# ######################## 
	
	
	# ## INSTALLED LIST QUERY ## #
	
	
	def get_installed_list(self):
		
		if self.search_process.is_alive():
			self.search_process.terminate()
		
		self.search_aborted=False
		self.show_loading()
		
		self.current_search_id=self.core.get_random_id()
		self.counter=0
		self.search_queue=multiprocessing.Queue()
		self.search_process=multiprocessing.Process(target=self.get_installed_list_thread,args=(self.search_queue,))
		
		self.search_process.daemon=True
		self.search_process.start()
		
		GLib.timeout_add(500, self.search_listener,self.current_search_id)
		
	#def search_package
	
	
	def get_installed_list_thread(self,search_queue):
		
		ret=self.core.store.get_installed_list()
		self.core.dprint("Search complete")
		search_queue.put(ret)

	#def search_package_thread
	
	
	# ##################### #
	
	
	

	# ## SCREENSHOTVIEWER FUNCTIONS ## ##############
	
	def window_size_changed(self,widget,allocation):
		
		x,y=self.window.get_size()
		self.popup_menu.popup_menu.set_size_request(400,y)
		self.screenshot_viewer.content_box.set_size_request(x,y)
		self.screenshot_viewer.sw.set_size_request(x-20,150)
		self.fade_box.set_size_request(x,y)
		
	#def window_size_allocation


	def screenshot_clicked(self,widget):

		if widget.get_children()[0].get_visible_child_name()=="image":
			
			if self.popup_menu.revealer.get_reveal_child():
				self.popup_menu.revealer.set_reveal_child(False)
				return
			
			if widget.get_children()[0].image_info["video_url"]==None:
				self.screenshot_viewer.set_screenshot(widget.get_children()[0].image_info["image_id"],self.details_box.screenshots_box)
			else:
				self.screenshot_viewer.set_screenshot(widget.get_children()[0].image_info["video_url"],self.details_box.screenshots_box,True)
				
			self.screenshot_viewer.revealer.set_reveal_child(True)
			
			
	#def screenshot_clicked
	
	# ####################################### #



	# ## POPUP MENU FUNCTIONS # #####################

	def main_eb_clicked(self,widget,event):
		
		if self.popup_menu.revealer.get_reveal_child():
			self.popup_menu.revealer.set_reveal_child(False)
			
		if self.fade_box_revealer.get_reveal_child():
			self.fade_box_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
			GLib.timeout_add(30,self.check_fade_out)
			self.fade_box_revealer.set_reveal_child(False)
			
	#def main_eb_clicked

	
	def menu_button_clicked(self,widget):
		
		self.fade_box_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
		self.popup_menu.revealer.set_reveal_child(not self.popup_menu.revealer.get_reveal_child())
		self.fade_box_revealer.set_reveal_child(True)
		
	#def menu_button_clicked


	def check_fade_out(self):
		
		if self.fade_box_revealer.get_child_revealed():
			return True
			
		self.fade_box_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
		
	#def check_fade_out
	
	# ########################################## #
	
	def get_load_status(self):
		ret=self.core.store.load_status()
		self.screenshot_viewer.buttons_box.hide()
		if ret==False:
			self.screenshot_viewer.buttons_box.show()
			self.screenshot_viewer.set_sensitive(True)
			self.screenshot_viewer.revealer.set_reveal_child(False)
			self.window.set_title("LliureX Store")

		return ret


	
	
	
#class LliurexStore

if __name__=="__main__":
	
	llx_store=LliurexStore()
