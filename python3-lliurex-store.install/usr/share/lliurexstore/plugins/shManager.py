import sys
import os
import stat
import locale
import tempfile
import subprocess
import urllib.request
import shutil
import time

class shmanager:
	def __init__(self):
		self.locale=locale.getlocale()[0]
		self.dbg=False
		self.plugin_actions={'install':'sh','pkginfo':'sh'}
		self.progress=0
		self.result={}
		self.result['data']=[]
		self.result['status']={}
		self.result['status']={'status':-1,'msg':''}
	#def __init__

	def set_debug(self,dbg=True):
		self.dbg=dbg
		self._debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Sh: %s'%msg)
	#def debug

	def register(self):
		return(self.plugin_actions)
	#def register

	def execute_action(self,action,applist):
		self.progress=0
		self.result['status']={'status':-1,'msg':''}
		count=len(applist)
		if (action):
			for app_info in applist:
				self._debug("Executing action "+action+" for "+str(app_info))
				if action=='install':
					self.result['data'].append(self._install_App(app_info))
				if action=='pkginfo':
					self.result['data'].append(self._get_Sh_Info(app_info))
		self.progress=100
		return(self.result)
	#def execute_action

	def _set_status(self,status,msg=''):
		self.result['status']={'status':status,'msg':msg}

	def _callback(self,partial_size=0,total_size=0):
		limit=99
		if partial_size!=0 and total_size!=0:
			inc=round(partial_size/total_size,2)*100
			self.progress=inc
		else:
			inc=1
			margin=limit-self.progress
			inc=round(margin/limit,3)
			self.progress=(self.progress+inc)
		if (self.progress>limit):
			self.progress=limit
	#def _callback

	def _install_App(self,app_info):
		return_msg=False
		app_url=app_info['installerUrl']
		self._debug("Checking availabilty for "+app_url)
		tmp_dir=tempfile.mkdtemp(None,None,'/tmp')
		file_name=app_url.split('/')[-1]
		dest_path=tmp_dir+'/'+file_name
		if self._download_App(app_url,dest_path):
			os.chdir(tmp_dir)
			os.chmod(dest_path, stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR)
			err=0
			try:
				sudo_cmd=['gksudo',dest_path]
				self._debug("executing "+str(sudo_cmd))
				launched_cmd=subprocess.Popen(sudo_cmd,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
#				launched_cmd=subprocess.check_output(sudo_cmd)
				cmd_launcher=os.path.basename(dest_path)
				cmd_launcher=os.path.splitext(cmd_launcher)[0]
				while launched_cmd.poll() is None:
					self._callback()
					time.sleep(0.4)
				if launched_cmd.poll():
					if launched_cmd.poll()==255:
						err=303
					else:
						err=launched_cmd.poll()
						err=3 #Force "package not installed" error
				cmd_status=launched_cmd.stdout.read()
				cmd_err=launched_cmd.stderr.read()
				self._debug("Error: "+str(cmd_err))
				self._debug("Result: "+str(cmd_status))
			except subprocess.CalledProcessError as callError:
#				err=callError.returncode
				#if gksudo fails set "permission denied" error
				err=303
			except Exception as e:
				self._debug(str(e))
				err=12
		else:
			err=11
		self._set_status(err)
		return app_info
	#def install_App

	def _download_App(self,app_url,dest_path=None):
		app_url.strip()
		if not dest_path:
			tmp_dir=tempfile.mkdtemp(None,None,'/tmp')
			dest_path=tmp_dir+'/'+app_url.split('/')[-1]
		self._debug("Downloading "+app_url+" to "+dest_path)	
		try:
#			urllib.request.urlretrieve(app_url,dest_path)
			with urllib.request.urlopen(app_url) as response, open(dest_path, 'wb') as out_file:
				bf=16*1024
				acumbf=0
				sh_size=int(response.info()['Content-Length'])
				while True:
					if acumbf>=sh_size:
						break
					shutil.copyfileobj(response, out_file,bf)
					acumbf=acumbf+bf
					self._callback(acumbf,sh_size)
			return_msg=True
		except Exception as e:
			self._debug(str(e))
			return_msg=False
		return return_msg
	#def _download_App

	def _get_Sh_Info(self,app_info):
		app_url=app_info['installerUrl']
		self._debug("Connecting to "+app_url)
		app_url.strip()
		try:
			info=urllib.request.urlopen(app_url) 
			app_info['size']=info.info()['Content-Length']
			err=0
		except:
			err=11
		self._set_status(err)
		return(app_info)

	#def _get_info

