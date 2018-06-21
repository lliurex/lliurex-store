#The name of the main class must match the file name in lowercase

#<---- Main scheme for a store plugin 
#Init: Could accept parameters if we declare them in storeManager's threads dict
class example:
	def __init__(self):
		self.dbg=False
		self.progress=0
		#This dict defines wich package_type relies on what action
		#actions could be defined in storeManager or per-plugin
		#Non contempled actions must declare its related functions on storeManager (threads dict) and define relationships with other actions in relatedActions.
		#package='*' (in this case action 'example' is related to all package_types. It could be "deb", "zmd" or whatever package type)
		self.plugin_actions={'example':'*'}
		#This switch enables cli_mode for the plugin, just in case some function difers from the gui mode (take a look at snapManager)
		self.cli_mode=False
		#This one controls if the plugin is enabled or not
		#It could be activated from two ways:
		# - storeManager having a parameter with name=package_type (simply add it to the arg list passed when invoking storeManager)
		# - Internal failure controls (see zmdManager for an example)
		#If there'll be no parameter for enable/disable then the plugin manages it's own state and self.disabled must be None
		#This example plugin is disabled by default
		self.disabled=True
	#def __init__
	
	#public function that sets the debug mode. If we execute storeManager in debug mode all plugins will be launched in this mode if propaate_debug==True
	def set_debug(self,dbg=True):
		self.dbg=int(dbg)
		self.debug ("Debug enabled")
	#def set_debug

	def _debug(self,msg=''):
		if self.dbg:
			print ('DEBUG Example: '+msg)
	#def debug

	#public function accessed by storemanager in order to register the plugin and its actions
	def register(self):
		#This function MUST return the dict with the action:package_type pair
		return(self.plugin_actions)

	#storeManager calls this method when launchs an action.
	def execute_action(self,action,applist):
		#applist is a list of appinfo elements
		#This function must return a dict with the dicts 'status' and 'data'
		#Status stores the returning status, 0=succesful, !0=error
		#Data stores the resulting data of the operation
		self.progress=0
		self.result['status']={'status':-1,'msg':''}
		self.result['data']=''
		if self.disabled:
			self._set_status(9)
		else:
			for app in applist:
				if action=='example':
					datalist.append(self._exec_example(app))
			self.result['data']=list(dataList)
			self.progress=100 #When all actions are launched we must assure that progress=100. 
		return(self.result)

	def _callback(self):
		self.progress=self.progress+1

#End of needed functions-------->

# Put your code ----> #

	def _exec_example(self,app):
		while (self.progress<100):
			self._callback()
		return(app)

# <---- #
