import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk,GdkPixbuf,GLib,GObject, Pango, Gdk

import os
import ImageManager
import Core
import Screenshot

import gettext
gettext.textdomain('lliurex-store')
_ = gettext.gettext


class SearchBox(Gtk.VBox):

	def __init__(self):
		
		Gtk.VBox.__init__(self)
		
		self.core=Core.Core.get_core()
		ui_path=self.core.ui_path
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-store')
		builder.add_from_file(ui_path)
			
		self.label_max_width=1
		
		self.description_label_ratio=0.091
		
		self.current_category=""
		self.current_pkg_list=[]
		
		self.search_box=builder.get_object("search_box2")
		self.search_box.set_name("DETAILS_BOX")
		self.results_search_box=builder.get_object("search_results_box")
		self.search_sw=builder.get_object("results_scrolledwindow")
		self.search_categories_box=builder.get_object("search_categories_box")
		self.categories_sw=builder.get_object("categories_scrolledwindow")
		
		self.add(self.search_box)
		self.show_all()
		
	#def init
	
	
	def populate_search_results(self,pkg_list,categories=None):
		

		for child in self.results_search_box.get_children():
			self.results_search_box.remove(child)
	
		for child in self.search_categories_box.get_children():
			self.search_categories_box.remove(child)
			
		# restore scroll bar to top
		self.search_sw.get_vadjustment().set_value(0)
		self.core.main_window.main_scroll.get_vadjustment().set_value(0)
		
		self.current_pkg_list=pkg_list
	
		if categories!=None:
			
			found_categories=set()
	
			for pkg in pkg_list:
				for category in categories:
					if category in pkg["categories"]:
						found_categories.add(category)
						break
		
			found_categories=list(sorted(found_categories))
			found_categories.insert(0,_("All"))
			
			counter=0
		
			for c in found_categories:
			
				hbox=Gtk.HBox()
				hbox.set_name("PKG_BOX")
				
				label=Gtk.Label(_(c))
				label.set_name("SHORT_DESCRIPTION")
				
				hbox.pack_start(label,True,True,5)
				
				
				b=Gtk.Button()
				b.set_name("RELATED_BUTTON")
				b.add(hbox)
				b.show_all()
				
				b.set_halign(Gtk.Align.FILL)
				
				if counter==0:
					c=None
				
				b.connect("clicked",self.filter_by,c)
				
				self.search_categories_box.pack_start(b,False,False,3)
				counter+=1
			
			self.categories_sw.show()
			
		else:
			self.categories_sw.hide()
		
		connect_size_request=True
		
		for pkg in pkg_list:
			
			self.add_pkg_to_list(pkg,connect_size_request)
			connect_size_request=False
			
		self.results_search_box.set_halign(Gtk.Align.FILL)
		self.results_search_box.show_all()
		
	#def populate_search_results
	
	
	def add_pkg_to_list(self,pkg,connect_size_request=False):
		
		item_box=Gtk.HBox()
		item_box.set_name("PKG_BOX")
			
		i={}
		i["x"]=64
		i["y"]=64
		i["aspect_ratio"]=True
		i["image_path"]=pkg["icon_uri"]
		i["name"]=pkg["name"]
		i["image_id"]=pkg["package"]+"_icon"
		s=Screenshot.ScreenshotNeo()
		s.set_from_file(i)
			
		vbox=Gtk.VBox()
			
		label=Gtk.Label(pkg["name"])
		label.set_name("RELATED_LABEL")
		label.set_valign(Gtk.Align.END)
		label.set_halign(Gtk.Align.START)
		label.set_ellipsize(Pango.EllipsizeMode.END)
		label.set_max_width_chars(self.label_max_width)
			
		description=Gtk.Label(pkg["summary"])
		description.set_name("SHORT_DESCRIPTION")
		description.set_valign(Gtk.Align.START)
		description.set_halign(Gtk.Align.START)
		description.set_ellipsize(Pango.EllipsizeMode.END)
		description.set_max_width_chars(self.label_max_width)
			
		vbox.pack_start(label,True,True,1)
		vbox.pack_start(description,True,True,1)
		vbox.set_halign(Gtk.Align.START)
			
		item_box.pack_start(s,False,False,5)
		item_box.pack_start(vbox,True,True,5)
			
		b=Gtk.Button()
		b.add(item_box)
		b.set_name("RELATED_BUTTON")
		b.set_valign(Gtk.Align.START)
		b.connect("clicked",self.result_clicked,pkg)
			
		b.set_size_request(0,80)
		
		if connect_size_request:
			b.connect("draw",self.search_item_size_request)
			
		self.results_search_box.pack_start(b,False,False,3)
		self.results_search_box.queue_draw()
		
		
	#def create_item
	
	def search_item_size_request(self,widget,data=None):
		
		allocation=widget.get_allocation()
		self.label_max_width=int(allocation.width*self.description_label_ratio)
		
		for child in self.results_search_box.get_children():
			child.get_child().get_children()[1].get_children()[0].set_max_width_chars(self.label_max_width*0.77)
			child.get_child().get_children()[1].get_children()[1].set_max_width_chars(self.label_max_width)
			
		if type(data)!=Gdk.Rectangle:
			widget.disconnect_by_func(self.search_item_size_request)
			widget.connect("size-allocate",self.search_item_size_request)
		
	#def search_item_size_request
	
	
	def filter_by(self,widget,filter):
		
		for child in self.results_search_box.get_children():
			self.results_search_box.remove(child)
		
		connect_size_request=True
		for pkg in self.current_pkg_list:
			
			if filter==None:
				self.add_pkg_to_list(pkg)
				continue
			if filter in pkg["categories"]:
				
				self.add_pkg_to_list(pkg,connect_size_request)
				connect_size_request=False
			
		self.results_search_box.show_all()
			
	#def filter_by
	
	
	def result_clicked(self,widget,pkg_data):
		
		a=widget.get_allocation()
		self.core.main_window.load_pkg_data(pkg_data["package"])
		
	#def result_clicked


#class SearchBox
