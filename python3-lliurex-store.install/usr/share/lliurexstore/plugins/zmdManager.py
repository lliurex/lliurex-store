import sys
import os
import subprocess
import stat
import locale
import tempfile
try:
	import xmlrpc.client as n4d
except ImportError:
	raise ImportError('xmlrpc not available. Disabling ZmdManager')
import ssl
import time

class zmdmanager:
	def __init__(self):
		self.locale=locale.getlocale()[0]
		self.dbg=False
		self.zmd_folder='/usr/share/zero-center/zmds'
		self.disabled=None
		if hasattr(sys,'last_value') or not (os.path.exists(self.zmd_folder)):
			#If there's an error at this point it only could be an importError caused by xmlrpc 
			print("ZMD support disabled")
			self.disabled=True
		self.plugin_actions={'install':'zmd','pkginfo':'zmd','remove':'zmd'}
		self.progress=0
		self.n4dclient=''
		self.result={}
		self.result['data']=[]
		self.result['status']={}
		self.result['status']={'status':-1,'msg':''}
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		#self._debug ("Debug enabled")
	#def set__debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Zmd: %s'%msg)
	#def _debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,action,applist):
		self.progress=0
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=list(applist)
		dataList=[]
		if self.disabled:
			self._set_status(9)
		else:
			count=len(applist)
			try:
				self.n4dclient=self._n4d_connect()
				for app_info in applist:
					if (action):
						if action=='install':
							dataList.append(self._install_Zmd(app_info))
						if action=='remove':
							dataList.append(self._remove_Zmd(app_info))
						if action=='pkginfo':
							dataList.append(self._get_Zmd_Info(app_info))
				self.result['data']=list(dataList)
			except:
				self.disabled=True
				self._set_status(10)
		self.progress=100
		return(self.result)
	#def execute_action
	
	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}
	#def _set_status
	
	def _callback(self,zmd_launcher):
		inc=1
		limit=99
		n4dvars=self.n4dclient.get_variable("","VariablesManager","ZEROCENTER")
		if zmd_launcher in n4dvars.keys():
			if n4dvars[zmd_launcher]['pulsating']:
				margin=limit-self.progress
				inc=round(margin/limit,3)
				self.progress=self.progress+inc
	#def _callback

	def _install_Zmd(self,app_info):
		zmd=self.zmd_folder+'/'+app_info['package']+'.zmd'
		#self._debug("Installing "+str(zmd))
		app_info=self._get_Zmd_Info(app_info)
		if app_info['state']=='installed':
			err=4
		else:
			if os.path.exists(zmd):
				err=0
				try:
					zmd_sudo=['pkexec',zmd]
					#self._debug("executing "+str(zmd_sudo))
					launched_zmd=subprocess.Popen(zmd_sudo,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
					zmd_launcher=os.path.basename(zmd)
					zmd_launcher=os.path.splitext(zmd_launcher)[0]
					while launched_zmd.poll() is None:
						self._callback(zmd_launcher)
						time.sleep(0.4)
					zmd_status=launched_zmd.stdout.read()
					zmd_err=launched_zmd.stderr.read()
					#self._debug("Error: "+str(zmd_err))
					#self._debug("Result: "+str(zmd_status))
				except Exception as e:
					#self._debug(str(e))
					pass
				finally:
					app_info=self._get_Zmd_Info(app_info)
					if app_info['state']!='installed':
						err=5
			else:
				err=8
		self._set_status(err)
		return(app_info)
	#def _install_Zmd

	def _remove_Zmd(self,app_info):
		zmd=app_info['package']+'.zmd'
		#self._debug("Removing "+str(zmd))
		os.chdir(self.zmd_folder)
		sw_continue=False
		err=0
		try:
			remove_packages=[]
			f=open(zmd,'r')
			for line in f:
				if 'PACKAGE_LIST=' in line:
					sw_continue=True
					packagelist=line.split('=')[-1]
					packagelist=packagelist.replace('"','')
					packagelist=packagelist[:-1]
					#We've the file with the packagelist, now it's time to read the list
					#self._debug("Obtaining packages in : "+packagelist)
					f2=open  (packagelist,'r')
					for line2 in f2:
						pkg=line2.split(' ')[0]
						pkg=pkg.split("\t")[0]
						pkg=pkg.replace('"','')
						#self._debug("Append to remove list: "+pkg)
						remove_packages.append(pkg)
					f2.close()
			f.close()
		except Exception as e:
			err=7
			print(str(e))
		if sw_continue:
			zmd_script='/tmp/zmd_script'
			f3=open(zmd_script,'w')
			f3.write('#!/bin/bash'+"\n")
			for pkg in remove_packages:
				f3.write('/usr/bin/zero-installer remove '+pkg+"\n")
			f3.write ("zero-center set-non-configured "+app_info['package']+"\n")
			f3.close()
			os.chmod(zmd_script,stat.S_IEXEC|stat.S_IREAD|stat.S_IWRITE|stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH|stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP)
#			zmd_sudo=['gksudo',zmd_script]
			zmd_sudo=['pkexec',zmd_script]
			try:
				self._debug("Executing "+str(zmd_sudo))
				zmd_launcher=os.path.basename(zmd)
				zmd_launcher=os.path.splitext(zmd_launcher)[0]
				launched_zmd=subprocess.Popen(zmd_sudo,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
				#self._debug("Launched")
				while launched_zmd.poll() is None:
					self._callback(zmd_launcher)
					time.sleep(0.2)
				zmd_status=launched_zmd.stdout.read()
				zmd_err=launched_zmd.stderr.read()
			except Exception as e:
				err=6
				#self._debug(str(e))
			#self._debug("Error: "+str(zmd_err))
			#self._debug("Result: "+str(zmd_status))
			app_info=self._get_Zmd_Info(app_info)
			if app_info['state']=='installed':
				err=6
			os.remove(zmd_script)
		else:
			err=6
		self._set_status(err)
		return(app_info)
	#def _remove_Zmd

	def _get_Zmd_Info(self,app_info):
		zmd=app_info['package']
		app_info['state']='Available'
		try:
			n4dvars=self.n4dclient.get_variable("","VariablesManager","ZEROCENTER")
			if n4dvars:
				self._set_status(0)
				for key in n4dvars:
					if zmd.lower() in key.lower():
						if 'state' in n4dvars[key]:
							if n4dvars[key]['state']==1:
								app_info['state']='installed'
			else:
				self._set_status(2)
		except Exception as e:
			self._set_status(10)
		return(app_info)
	#def _get_Zmd_Info
	
	def _n4d_connect(self):
		#Setup SSL
		context=ssl._create_unverified_context()
		n4dclient = n4d.ServerProxy("https://localhost:9779",context=context)
		return(n4dclient)
	#def _n4d_connect
