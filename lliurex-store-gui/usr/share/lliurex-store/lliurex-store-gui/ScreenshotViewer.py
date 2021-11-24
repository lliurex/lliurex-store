import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk,GdkPixbuf,GLib,Gdk,WebKit2 as WebKit
import Screenshot


class ScreenshotViewer(Gtk.EventBox):

	def __init__(self):
	
		Gtk.EventBox.__init__(self)
		self.set_valign(Gtk.Align.START)
		self.set_halign(Gtk.Align.START)

		self.html_skel='<html><body bgcolor=black><div align=center><iframe height=97% width=90% align=center src="%%URL%%" frameborder="0" allowfullscreen></iframe></div></body></html>'		
		self.border=20
		
		try:
			cache_dir=os.environ["XDG_CACHE_HOME"]
		except:
			cache_dir=os.path.expanduser("~/.cache/")
		
		self.image_dir=cache_dir+"/lliurex-store/"
		
		
		self.revealer=Gtk.Revealer()
		self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
		self.revealer.set_transition_duration(500)
		

		self.content_box=Gtk.VBox()
		self.content_box.set_name("POPUP_SHADOW_TOPBOTTOM")
		hbox=Gtk.HBox()
		
		self.image=Screenshot.ScreenshotNeo()
		self.wv=WebKit.WebView()
		
		self.wv=WebKit.WebView()
		self.w_vp=Gtk.Viewport()
		self.w_sw=Gtk.ScrolledWindow()
		self.w_vp.add(self.w_sw)
		self.w_sw.add(self.wv)
		
		self.image.add_titled(self.w_vp,"html","Html")
		
		
		hbox.pack_start(self.image,True,True,self.border)
		self.content_box.pack_start(hbox,True,True,self.border)
		
		self.buttons_box=Gtk.HBox()
		self.buttons_box.set_valign(Gtk.Align.CENTER)
		
		
		for x in range(0,4):
			b=Gtk.Button(str(x))
			b.set_size_request(100,100)
			b.set_name("RELATED_BUTTON")
			self.buttons_box.pack_start(b,False,False,5)
			
		self.sw=Gtk.ScrolledWindow()
		
		self.vp=Gtk.Viewport()
		self.vp.set_halign(Gtk.Align.CENTER)
		self.sw.add(self.vp)
		self.sw.set_halign(Gtk.Align.CENTER)
		self.sw.set_margin_bottom(30)
		self.vp.add(self.buttons_box)
		
		self.content_box.pack_end(self.sw,False,False,0)

		self.revealer.add(self.content_box)
		self.revealer.show_all()
		self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
		self.connect("button-press-event",self.area_clicked)
		
		self.add(self.revealer)
	
	#def init
	
	
	def wait_to_reveal(self,x,y,data,url=False):
		
		if not self.revealer.get_child_revealed():
			
			return True
		
		if url==False:
			image_info={}
			image_info["x"]=x
			image_info["y"]=y
			image_info["pixbuf"]=data
			image_info["aspect_ratio"]=True
			self.image.set_from_pixbuf(image_info)
		else:
			self.show_url(None,data)
			
	#def wait_to_reveal
	
	
	def set_screenshot(self,current_id,screenshots_box,current_id_is_url=False):

		self.image.spinner.start()
		self.image.spinner.show()
		self.image.set_visible_child_name("spinner")
		
		for child in self.buttons_box.get_children():
			
			self.buttons_box.remove(child)
		
		for x in screenshots_box:
			
			tmp=x.get_children()[0]
			pixbuf=tmp.image.get_pixbuf()
			id=x.get_children()[0].image_info["image_id"]
			b=Gtk.Button()
			b.add(Gtk.Image.new_from_pixbuf(pixbuf))
			if tmp.image_info["video_url"]!=None:
				b.connect("clicked",self.show_url,tmp.image_info["video_url"])
			else:
				b.connect("clicked",self.screenshot_button_clicked,id)
			b.set_size_request(100,100)
			b.set_name("RELATED_BUTTON")
			self.buttons_box.pack_start(b,False,False,5)
			self.buttons_box.show_all()
		
		
		if not current_id_is_url:
		
			image=Gtk.Image.new_from_file(self.image_dir+current_id)
			
			pixbuf=image.get_pixbuf()
			if pixbuf:
				x=pixbuf.get_width()
				y=pixbuf.get_height()
				
				w_x,w_y=self.content_box.get_size_request()
				w_x-=self.border*2 
				w_y-=self.border*2 + 240
				
				ratio=min(w_x*1.0/x,w_y*1.0/y)
				pixbuf=pixbuf.scale_simple(x*ratio,y*ratio,GdkPixbuf.InterpType.BILINEAR)
				
				new_x=x*ratio
				new_y=y*ratio
			else:
				new_x=0
				new_y=0
			
			GLib.timeout_add(30,self.wait_to_reveal,new_x,new_y,pixbuf,False)
			
		else:
			
			new_x=0
			new_y=0
			GLib.timeout_add(30,self.wait_to_reveal,new_x,new_y,current_id,True)
			
	#def set_screenshot
	
	
	def show_url(self,widget,url):
		
		self.wv.load_html_string(self.html_skel.replace("%%URL%%",url),"")
		self.image.set_visible_child_name("html")
		
	#def show url


	def screenshot_button_clicked(self,widget,current_id):
		
		image=Gtk.Image.new_from_file(self.image_dir+current_id)
		
		pixbuf=image.get_pixbuf()
		x=pixbuf.get_width()
		y=pixbuf.get_height()
		
		w_x,w_y=self.content_box.get_size_request()
		w_x-=self.border*2 
		w_y-=self.border*2 + 240
		
		ratio=min(w_x*1.0/x,w_y*1.0/y)
		
		new_x=x*ratio
		new_y=y*ratio
		
		pixbuf=pixbuf.scale_simple(x*ratio,y*ratio,GdkPixbuf.InterpType.BILINEAR)
		self.image.spinner.hide()
		
		image_info={}
		image_info["x"]=new_x
		image_info["y"]=new_y
		image_info["pixbuf"]=pixbuf
		image_info["aspect_ratio"]=True
		self.image.set_from_pixbuf(image_info)
		
		self.image.set_from_pixbuf(image_info)

	#def screenshot_button_clicked

	
	def area_clicked(self,widget,event):
		
		self.revealer.set_reveal_child(False)

	#def area_clicked


#class ScreenshotViewer
