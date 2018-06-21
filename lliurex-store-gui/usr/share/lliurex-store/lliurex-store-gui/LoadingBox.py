import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Pango, GdkPixbuf, Gdk, Gio
import Screenshot
import ImageManager

import Core

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


import gettext
gettext.textdomain('lliurex-store')
_ = gettext.gettext


class LoadingBox(Gtk.VBox):
	
	def __init__(self):
		
		Gtk.VBox.__init__(self)
		
		self.core=Core.Core.get_core()
		ui_path=self.core.ui_path
		
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-store')
		builder.add_from_file(ui_path)
		

		self.loading_box=builder.get_object("loading_box")
		self.l1_box=builder.get_object("l1_box")
		self.l2_box=builder.get_object("l2_box")
		self.i_box=builder.get_object("i_box")
		self.u_box=builder.get_object("u_box")
		self.r_box=builder.get_object("r_box")
		self.e_box=builder.get_object("e_box")
		self.x_box=builder.get_object("x_box")
		
		self.loading_label=builder.get_object("loading_label")
		self.add(self.loading_box)
		
		self.set_css_info()
		self.show_all()
		
	#def init

	
	def set_css_info(self):
		
		self.style_provider=Gtk.CssProvider()
		f=Gio.File.new_for_path(self.core.rsrc_dir+"lliurex-store.css")
		self.style_provider.load_from_file(f)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
		self.l1_box.set_name("L1_BOX")
		self.l2_box.set_name("L2_BOX")
		self.i_box.set_name("I_BOX")
		self.u_box.set_name("U_BOX")
		self.r_box.set_name("R_BOX")
		self.e_box.set_name("E_BOX")
		self.x_box.set_name("X_BOX")
		
		self.loading_label.set_name("SHORT_DESCRIPTION")
		
	#def set_css_info

	
#class LoadingBox
