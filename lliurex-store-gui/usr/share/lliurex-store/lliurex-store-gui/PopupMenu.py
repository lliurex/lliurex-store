import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk,GdkPixbuf,Gdk

import Core

import gettext
gettext.textdomain('lliurex-store')
_ = gettext.gettext



class PopupMenu(Gtk.EventBox):

	def __init__(self):

		self.core=Core.Core.get_core()
		ui_path=self.core.ui_path
		
		popup_menu_x=400
		popup_menu_y=765
		percentage=0.8
		shadow_size=50
		
		Gtk.EventBox.__init__(self)
		self.set_valign(Gtk.Align.START)
		self.set_halign(Gtk.Align.START)
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-store')
		builder.add_from_file(ui_path)
		
		
		self.revealer=Gtk.Revealer()
		self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
		self.revealer.set_transition_duration(500)
		
		self.popup_image=builder.get_object("popup_image")
		self.popup_menu=builder.get_object("popup_box")
		self.popup_menu_left=builder.get_object("popup_box_left")
		self.popup_shadow=builder.get_object("popup_box_right")
		decorator_bar=builder.get_object("decoration_bar_box")
		
		eventbox=builder.get_object("eventbox1")
		eventbox.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
		eventbox.connect("button-press-event",self.hide_revealer)
		
		image=Gtk.Image.new_from_file(self.core.rsrc_dir+"lliurex-default-background.png")
		pixbuf=image.get_pixbuf()
		original_ratio=pixbuf.get_width(),pixbuf.get_height()
		pixbuf=pixbuf.scale_simple(400*percentage,225*percentage,GdkPixbuf.InterpType.BILINEAR)
		self.popup_image.set_from_pixbuf(pixbuf)
		
		self.revealer.add(self.popup_menu)
		self.add(self.revealer)
		

		self.popup_menu.set_name("TRANSPARENT")
		self.popup_shadow.set_name("POPUP_SHADOW_LEFTRIGHT")
		self.revealer.set_name("TRANSPARENT")
		self.popup_menu_left.set_name("DROPMENU")
		decorator_bar.set_name("DECORATOR_BAR")
		
		self.populate_menu()
		
	#def init
	
	
	def populate_menu(self):
		
		
		b=Gtk.Button()
		hbox=Gtk.HBox()
		
		b.icon=self.core.rsrc_dir+"icons/small_icons/home.svg"
		b.icon_over=self.core.rsrc_dir+"icons/small_icons/home_white.svg"
		txt=_("Home")
			
		b.img=Gtk.Image.new_from_file(b.icon)
		b.img.set_margin_left(5)
		b.label=Gtk.Label(txt)
		b.label.set_halign(Gtk.Align.START)
			
		hbox.pack_start(b.img,False,False,0)
		hbox.pack_start(b.label,False,False,20)
		b.add(hbox)
			
		b.add_events( Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK )
		b.connect("motion-notify-event",self.mouse_over)
		b.connect("leave_notify_event",self.mouse_left)
		b.connect("clicked",self.go_home)
			
		b.show_all()
		b.set_name("SECTION_BOX")
		self.popup_menu_left.pack_start(b,True,True,0)

		b=Gtk.Button()
		hbox=Gtk.HBox()
		
		b.icon=self.core.rsrc_dir+"icons/small_icons/favorite.svg"
		b.icon_over=self.core.rsrc_dir+"icons/small_icons/favorite_white.svg"
		txt=_("My applications")
			
		b.img=Gtk.Image.new_from_file(b.icon)
		b.img.set_margin_left(5)
		b.label=Gtk.Label(txt)
		b.label.set_halign(Gtk.Align.START)
			
		hbox.pack_start(b.img,False,False,0)
		hbox.pack_start(b.label,False,False,20)
		b.add(hbox)
			
		b.add_events( Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK )
		b.connect("motion-notify-event",self.mouse_over)
		b.connect("leave_notify_event",self.mouse_left)
		b.connect("clicked",self.get_installed_list)
			
		b.show_all()
		b.set_name("SECTION_BOX")
		self.popup_menu_left.pack_start(b,False,False,0)

		separator=Gtk.Separator()
		separator.set_name("SECTION_DIVIDER")
		self.popup_menu_left.pack_start(separator,False,False,0)
		
		for item in sorted(self.core.categories_manager.categories):
			
			b=Gtk.Button()
			hbox=Gtk.HBox()
		
			b.icon=self.core.categories_manager.categories[item]["small_icon"]
			b.icon_over=self.core.categories_manager.categories[item]["small_icon_over"]
			txt=_(item)
			
			b.img=Gtk.Image.new_from_file(b.icon)
			b.img.set_margin_left(5)
			b.label=Gtk.Label(txt)
			b.label.set_halign(Gtk.Align.START)
			
			hbox.pack_start(b.img,False,False,0)
			hbox.pack_start(b.label,False,False,20)
			b.add(hbox)
			
			b.add_events( Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK )
			b.connect("motion-notify-event",self.mouse_over)
			b.connect("leave_notify_event",self.mouse_left)
			
			b.show_all()
			b.set_name("SECTION_BOX")
			
			b.connect("clicked",self.category_clicked,item)
			
			self.popup_menu_left.pack_start(b,True,True,0)
			
	#def populate_menu
		
	
	def mouse_over(self,widget,event):
		
		widget.img.set_from_file(widget.icon_over)
		
	#def mouse_over
	
	
	def mouse_left(self,widget,event):
		
		widget.img.set_from_file(widget.icon)
		
	#def mouse_left
	

	def hide_revealer(self,widget,event):
		
		self.core.main_window.main_eb_clicked(None,None)
		
	#def hide_revealer
	
	
	def category_clicked(self,widget,category):
		
		self.core.main_window.main_eb_clicked(None,None)
		self.core.main_menu.category_clicked(None,category)
		
	#def category_clicked
	
	
	def get_installed_list(self,widget):
		
		self.core.main_window.main_eb_clicked(None,None)
		self.core.main_window.get_installed_list()
		
	#def get_installed_list
	
	
	def go_home(self,widget):
		
		self.core.main_window.show_home()
		# Forcing main_eb_clicked call to hide both popup menu and fade_box
		self.core.main_window.main_eb_clicked(None,None)
		self.core.main_window.stack.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
		
	#def go_home
	

#class PopupMenu
