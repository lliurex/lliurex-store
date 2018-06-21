import os
import gi
from gi.repository import Gio
gi.require_version('AppStreamGlib', '1.0')
from gi.repository import AppStreamGlib as appstream
import subprocess
import json
import re
import urllib
import random
import threading
import time
import datetime
import gettext
from bs4 import BeautifulSoup

class loadstore:
	def __init__(self):
		self.dbg=False
		self.plugin_actions={'load':'*'}
		self.store=''
		self.progress=0
		self.error=0
#		self.zmd_store_dir='/var/lib/lliurexstore/zmds' #DEPRECATED
		self.result={}
		self.result['data']={}
		self.result['status']={}
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Load: %s'%msg)
	#def _debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,action,store=None,loadBundles=False):
		self.progress=0
		if store:
			self.store=store
		else:
			self.store=appstream.Store()
		if action=='load':
			self._load_store(self.store)
		if action=='load_bundles':
			self._load_store(self.store,loadBundles=True)
		self.result['data']=self.store
		self.progress=100
		return(self.result)
	#def execute_action

	def get_error(self):
		return (self.error)
	#def get_error

	def _load_store(self,store,loadBundles=False):
		icon_dir='/usr/share/icons/hicolor/128x128'
		flags=[appstream.StoreLoadFlags.APP_INFO_SYSTEM,appstream.StoreLoadFlags.APP_INSTALL,appstream.StoreLoadFlags.APP_INFO_USER,appstream.StoreLoadFlags.DESKTOP,appstream.StoreLoadFlags.APPDATA,appstream.StoreLoadFlags.ALLOW_VETO]
		for flag in flags:
			try:
				self._debug("Loading "+str(flag))
				store.load(flag)
			except:
				print ("Failed to load"+str(flag))
				pass
		#Zomandos are now available from appstream
#		store=self.load_zmds_catalog(store)
		store=self._sanitize_store(store)
		self.store=store
		return(store)
	#def load_store

	def load_zmds_catalog(self,store): #DEPRECATED
		if os.path.exists(self.zmd_store_dir):
			store=self._generic_file_load(self.zmd_store_dir,store)
		return(store)
	#def load_zmds_catalog(self)

	def _generic_file_load(self,target_dir,store):
		icon_dir='/usr/share/icons/hicolor/128x128'
		files=os.listdir(target_dir)
		for target_file in os.listdir(target_dir):
			if target_file.endswith('appdata.xml'):
				store_file=Gio.File.new_for_path(target_dir+'/'+target_file)
				self._debug("Adding file %s/%s"%(target_dir,target_file))
				try:
					store.from_file(store_file,icon_dir,None)
				except Exception as e:
					self._debug("Couldn't add file %s to store"%target_file)
					self._debug("Reason: %s"%e)
		return(store)
	
	def _parse_desktop(self,store): #DEPRECATED. Loads the apps from the available desktop files 
		desktop_dir='/usr/share/applications'
		applist=[]
		for desktop_file in os.listdir(desktop_dir):
			if desktop_file.endswith('desktop'):
				a=appstream.App()
				try:
					a.parse_file(desktop_dir+'/'+desktop_file,16)
					a.set_priority(0)
					for veto in a.get_vetos():
						a.remove_veto(veto)
					store.add_app(a)
					self._debug("Adding app from desktop %s"%desktop_file)
				except:
					pass
		return(store)
	#def _parse_desktop

	def _sanitize_store(self,store):
		applist=store.get_apps()
		tmp_store_apps={}
		lliurex_apps={}
		zmd_apps=[]
		for app in applist:
			#Zomandos get max priority
			if app.has_category('Zomando'):
				self._debug("Prioritize zmd %s"%app.get_id())
				app.set_priority(400)
				lliurex_apps.update({app.get_id_filename():app})
				id_app=str(app.get_id_filename()).replace('zero-lliurex-','')
				zmd_apps.append(id_app)
			#Prioritize Lliurex apps
			elif app.has_category('Lliurex'):
				self._debug("Prioritize app %s"%app.get_id())
				app.set_priority(200)
				lliurex_apps.update({app.get_id_filename():app})
			elif str(app.get_origin()).find('lliurex')>=0:
				self._debug("Prioritize app %s"%app.get_id())
				app.set_priority(100)
				lliurex_apps.update({app.get_id_filename():app})
			else:
				app.set_priority(0)
				if app.get_id_filename() in lliurex_apps.keys():
					self._debug("Mergin app %s as is in LliureX"%app.get_id())
					lliurex_apps[app.get_id_filename()].subsume_full(app,appstream.AppSubsumeFlags.BOTH_WAYS)
#					store.add_app(lliurex_apps[app.get_id_filename()])
			#Remove apps whitout pkgname
			if not app.get_pkgnames():
				store.remove_app(app)
			#Remove add-on apps (as are included in the main packages)
			if app.get_kind()==appstream.AppKind.ADDON:
				self._debug("Removed addon %s"%app.get_pkgnames())
				store.remove_app(app)
			#Remove duplicated apps 
			#Unlike gnome-store we'll try to compare the info of the package in order of discard only the "part-of" packages
			pkg=app.get_pkgname_default()
			if pkg in tmp_store_apps.keys():
				fn=app.get_id_no_prefix()
				self._debug("Comparing %s with %s"%(fn,tmp_store_apps[pkg]['fn']))
				if fn != tmp_store_apps[pkg]['fn']:
					if fn != pkg and ".desktop" not in fn:
						self._debug("Removed duplicated %s"%app.get_id())
						store.remove_app(app)
					else:
						self._debug("Removed duplicated %s"%tmp_store_apps[pkg]['app'].get_id())
						store.remove_app(tmp_store_apps[pkg]['app'])
						tmp_store_apps.update({pkg:{'fn':app.get_id_no_prefix(),'app':app}})
			elif pkg:
#				self._debug("Adding "+app.get_id_filename()+" to uniq dict")
				tmp_store_apps.update({pkg:{'fn':app.get_id_filename(),'app':app}})
		#Delete zomando-related debs
		store=self._purge_zomandos(zmd_apps,store)
		#Check the blacklist
		store=self._apply_blacklist(store)
		return (store)
	#def _sanitize_store

	def _purge_zomandos(self,zmd_apps,store):
		for zmd_id in zmd_apps:
			self._debug("Searching debs related to %s"%zmd_id)
			purge_list=store.get_apps_by_id(zmd_id)
			purge_list.extend(store.get_apps_by_id(zmd_id+".desktop"))
			for purge_app in purge_list:
				if purge_app:
					if not purge_app.has_category('Zomando'):
						self._debug("Removed related zomando app %s"%purge_app.get_id())
						store.remove_app(purge_app)
		return(store)
	#def _purge_zomandos

	def _apply_blacklist(self,store):
		try:
			flavour=subprocess.check_output(["lliurex-version","-f"]).rstrip()
			flavour=flavour.decode("utf-8")
			if flavour=='None':
				self._debug("Unknown flavour. Switching to desktop")
				flavour='desktop'
		except (subprocess.CalledProcessError,FileNotFoundError) as e:
				self._debug("Running on a non Lliurex host")
				flavour='desktop'
		try:
			if os.path.isfile('/usr/share/lliurex-store/files/blacklist.json'):
				blFile=open('/usr/share/lliurex-store/files/blacklist.json').read()
				blacklist=json.loads(blFile)
				blacklist_apps=[]
				if flavour in blacklist:
					blacklist_apps=blacklist[flavour]
				if "all" in blacklist:
					blacklist_apps.extend(blacklist["all"])
				blacklist_re=[]
				for blacklist_app in blacklist_apps:
					self._debug("Blacklisted app: "+blacklist_app)
					re_result=re.search('([^a-zA-Z0-9_-])',blacklist_app)
					if re_result:
						if blacklist_app[0]=='*':
							blacklist_app='.'+blacklist_app
						blacklist_re.append("("+blacklist_app+")")
					else:
						app=store.get_app_by_pkgname(blacklist_app)
						if app:
							self._debug("Removed "+str(app))
							store.remove_app(app)
						else:
							self._debug("App %s from blacklist not found in store. Assigned to RE blacklist"%blacklist_app)
							blacklist_re.append("("+blacklist_app+")")
				if blacklist_re:
					self._debug("Attempting to remove apps by RE match")
					for app in store.get_apps():
						for blacklist_app in blacklist_re:
							re_result=re.search(blacklist_app,app.get_id())
							if re_result:
								store.remove_app(app)
								self._debug("Removed %s as matches with %s"%(app.get_id(),blacklist_app))
			else:
				self._debug('No blacklist to check')
		except Exception as e:
			self._debug("Error processing blacklist: %s"%e)
		finally:
			return(store)
	#def _apply_blacklist

