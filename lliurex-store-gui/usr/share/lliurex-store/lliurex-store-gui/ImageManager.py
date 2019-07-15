import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

import cairo

from gi.repository import Gtk,GdkPixbuf,GLib,Gdk, PangoCairo, Pango


def scale_image(image_file,x,y,aspect_ratio=True):

	image=Gtk.Image.new_from_file(image_file)
	pixbuf=image.get_pixbuf()
	if not pixbuf:
		image=Gtk.Image.new_from_file("/usr/share/icons/breeze/mimetypes/64/image-png.svg")
		pixbuf=image.get_pixbuf()
	img_x=pixbuf.get_width()
	img_y=pixbuf.get_height()
	if aspect_ratio:
		
		ratio=min(x*1.0/img_x,y*1.0/img_y)
	else:
		ratio=1
		img_x=x
		img_y=y
	
	pixbuf=pixbuf.scale_simple(img_x*ratio,img_y*ratio,GdkPixbuf.InterpType.HYPER)
	img=Gtk.Image.new_from_pixbuf(pixbuf)
	
	return img
	
#def scale_image


def scale_pixbuf(pixbuf,x,y,aspect_ratio=True):
	
	img_x=pixbuf.get_width()
	img_y=pixbuf.get_height()
	if aspect_ratio:
		
		ratio=min(x*1.0/img_x,y*1.0/img_y)
	else:
		ratio=1
		img_x=x
		img_y=y
	
	pixbuf=pixbuf.scale_simple(img_x*ratio,img_y*ratio,GdkPixbuf.InterpType.BILINEAR)
	return pixbuf
	
#def scale_pixbuf
	

def create_banner(icon_file,size_x,size_y,txt,frame=True,output_file=None):
	
	reduction_percentage=0.65
	if not frame:
		reduction_percentage=0.9
		
	offset_x= (size_x - (size_x*reduction_percentage)) /2
	offset_y= (size_y - (size_y*reduction_percentage)) /2
	
	image=scale_image(icon_file,size_x*reduction_percentage,size_y*reduction_percentage,frame)
	pixbuf=image.get_pixbuf()

	surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,size_x,size_y)
	ctx=cairo.Context(surface)
	
	lg1 = cairo.LinearGradient(0.0,0.0, 0.0, size_y)
	lg1.add_color_stop_rgba(0, 0/255.0, 95/255.0, 219/255.0, 1)
	lg1.add_color_stop_rgba(1, 0/255.0, 56/255.0, 134/255.0, 1)
	ctx.rectangle(0, 0, size_x, size_y)
	ctx.set_source(lg1)
	ctx.fill()
	
	img_offset_x=offset_x
	img_offset_y=offset_y
	
	label_space_percentage=1.5
	if txt==None:
		label_space_percentage=1
	
	Gdk.cairo_set_source_pixbuf(ctx,image.get_pixbuf(),img_offset_x,img_offset_y/label_space_percentage)
	ctx.paint()
	
	if txt!=None and len(txt) >1:
		
		ctx.set_source_rgba( 0,0,0,0.7 )
		ctx.rectangle(0, size_y-offset_y , size_x, offset_y)
		ctx.fill()
		
		pctx = PangoCairo.create_layout(ctx)
		desc = Pango.font_description_from_string ("Roboto %s"%int(offset_y*0.5))
		pctx.set_font_description(desc)
		ctx.set_source_rgba(0.9,0.9,0.9,1)
		
		if len(txt)> 18:
			txt=txt[0:15]+"..."
		
		pctx.set_markup("%s"%txt)
		text_x,text_y=pctx.get_pixel_size()
		ctx.move_to(size_x/2 - text_x/2, size_y - offset_y )
		PangoCairo.show_layout(ctx, pctx)
	
	px=Gdk.pixbuf_get_from_surface(surface,0,0,size_x,size_y)
	img=Gtk.Image.new_from_pixbuf(px)
	
	
	if output_file == None:
		return [True,img]
	else:
		surface.write_to_png(output_file)
		return [True,output_file]
	
	
#def create_banner

if __name__=="__main__":
	
	create_banner("/usr/share/icons/Antu/apps/48/mozilla-firefox.svg",200,200,"Firefox")
