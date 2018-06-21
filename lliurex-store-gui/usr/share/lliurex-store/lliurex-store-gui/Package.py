import Core

class Package(dict):
	
	
	def __init__(self,dic):
		dict.__init__(self)
		
		for key in dic:
			
			self[key]=dic[key]
		
		self.fix_info()
		
	# __init__
	
	def fix_info(self):
		
		self["categories"]=self.setdefault("categories",[])
		self["component"]=self.setdefault("component","")
		self["depends"]=self.setdefault("depends",)
		self["description"]=self.setdefault("description","")
		self["extraInfo"]=self.setdefault("extraInfo","")
		self["homepage"]=self.setdefault("homepage",)
		self["icon"]=self.setdefault("icon","")
		self["id"]=self.setdefault("id","")
		self["installerUrl"]=self.setdefault("installerUrl","")
		self["kudos"]=self.setdefault("kudos","")
		self["license"]=self.setdefault("license","")
		self["name"]=self.setdefault("name","")
		self["package"]=self.setdefault("package","")
		
		self["screenshots"]=self.setdefault("screenshots",[])
		self["state"]=self.setdefault("state","")
		self["suggests"]=self.setdefault("suggests","")
		self["summary"]=self.setdefault("summary","")
		self["thumbnails"]=self.setdefault("thumbnails",[])
		self["version"]=self.setdefault("version","")
		self["videos"]=self.setdefault("videos",[])
		
		if "video" in self:
			if  self["video"] not in self["videos"]:
				if type(self["video"])==type(""):
					if len(self["video"]) >0:
						video={}
						video["url"]=self["video"]
						video["preview"]=""
						self["video"]=video
						
						self["videos"].append(video)
		
		for v in self["videos"]:
			v["preview"]=v.setdefault("preview","")
			v["url"]=v.setdefault("url","")

		self["banner_large"]=self.setdefault("banner_large",None)
		self["banner_small"]=self.setdefault("banner_small",None)
		
		try:
			self["category"]=self.setdefault("category",self["categories"][0])
		except:
			self["category"]=self.setdefault("category","")
			
		self["size"]=self.setdefault("size","")
		self["related_packages"]=self.setdefault("related_packages",[])
		
		for r in self["related_packages"]:
			r["name"]=r.setdefault("name","")
			r["banner"]=r.setdefault("banner",None)
			r["package"]=r.setdefault("package","")
			r["icon"]=r.setdefault("icon","")
			r["component"]=r.setdefault("component","main")
		
		self["icon_uri"]=Core.Core.get_core().resources.get_icon(self)
		
	#def fix_info
