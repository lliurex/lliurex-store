#!/usr/bin/python3
import sys
import argparse
#sys.path.append('/usr/share/lliurex-store')
#sys.path.append('/home/lliurex/lliurex-store/trunk/fuentes/lliurex-appstore.install/usr/share/lliurex-store')
import lliurexstore.storeManager as storeManager
import time
import html2text
import gettext
gettext.textdomain('python3-lliurex-store')
_=gettext.gettext

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def main():
	def print_results(action=None):
		printed=False
		results=store.get_result(action)
		status=store.get_status(action)
		print("ST: %s"%status)
		if not 'status' in status.keys():
			status['status']=1
			status['msg']='package not found'
		processed=[]
		print ("")
		for action in results.keys():
			if action in actions and not actionList[action]:
				if status['status']==0:
					print (_(u"Results for ")+_(action))
					for data in results[action]:
						if action=='info':
							try:
								print(color.DARKCYAN+_(u'Package')+': '+color.END + data['package'])
								print(_(u'Name')+': '+data['name'])
								print(_(u'ID')+': '+data['id'])
								print(_(u'Version')+': '+data['version'])
								print(_(u'Size')+': '+data['size'])
								print(_(u'License')+': '+data['license'])
								listCat=[]
								for cat in data['categories']:
									listCat.append(_(cat))
								print(_(u'Categories')+': '+','.join(listCat))
								msg=''
								if data['state']=='installed':
									msg=_('installed')
								else:
									msg=_('available')
								if data['updatable']:
									msg +=_(' (updatable)')
								print(_(u'Status')+': '+msg)
								print(_(u'Summary')+': '+data['summary'])
								desc=(html2text.html2text(data['description'],"lxml"))
								print(_(u'Description')+': '+desc)
								pkgString=[]
								for dependency in data['depends']:
										pkgName=dependency.split(';')[0]
										pkgString.append(pkgName)
								print(_(u'Depends')+': '+', '.join(pkgString))
								print("")
							except Exception as e:
								print("CLI: Error printing key %s"%e)
						elif action=='search':
							#Only print name and summary
							printcolor=color.DARKCYAN
							data_id=''
							if data['bundle']!='':
								printcolor=color.PURPLE
							elif (data['package'] not in data['id'] or data['package'] in processed):
								data_id=" (%s)"%data['id']
							else:
								processed.append(data['package'])
							print("%s%s%s%s: %s"%(printcolor,data['package'],data_id,color.END,data['summary']))

						elif action=='list':
							#Print package, summary and status
							try:
								if data['package']:
									package=data['package']
								else:
									package=data['name']
								if data['state']=='installed':
									msg=_('installed')
								else:
									msg=_('available')
								print(color.DARKCYAN+package+color.END+": "+data['summary']+' ('+','.join(data['categories'])+')'+' ('+msg+')')
							except Exception as e:
								print(_(u'Error listing')+ ':'+str(e))
								pass
						elif action=='install':
								print(data['package']+" "+ _(u"installed")+" "+color.BOLD+ _(u"succesfully")+color.END)
						elif action=='remove':
								print(data['package']+" "+ _(u"removed")+" "+color.BOLD+ _(u"succesfully")+color.END)
						else:
							print("RESULT:\n%s"%data)
				else:
					msg=_(u"Unable to")+' '+_(action)
					failed=parms[action]
					if (action=='search' or action=='info'):
							msg=_(u"Unable to show")
					if action=='list':
							failed=', '.join(failed)

					print (color.RED+_(u"Error")+": "+color.END+msg+' '+failed+' ('+_(status['msg'])+')')
				printed=True
		return(printed)
	#def print_results

	CURSOR_UP='\033[F'
	ERASE_LINE='\033[K'
	actions=[]
	parms={}
	dbg=False
	appimage=False
	snap=False
	args=process_Args(sys.argv)
#	if args.debug:
#		dbg=True
	if args.appimage:
		appimage=True
	if args.snap:
		snap=True
	if args.view:
		actions.append('info')
		parms['info']=args.view
	if args.search:
		actions.append('search')
		parms['search']=args.search
	if args.install:
		actions.append('install')
		parms['install']=args.install
	if args.remove:
		actions.append('remove')
		parms['remove']=args.remove
#	if args.random:
#		actions.append('random')
#		parms['random']=args.random
#	if args.list:
#		actions.append('list')
#		parms['list']=args.list

	actionList={'search':False,'info':False,'pkgInfo':False,'install':False,'remove':False,'list':False,'list-sections':False,'random':False}
	start_time=time.time()
	store=storeManager.StoreManager(appimage=appimage,snap=snap,dbg=dbg,cli=True)
	for action in actions:
		store.execute_action(action,parms[action])
		actionList[action]=False
		
	while store.is_action_running():
		progressDic=store.get_progress()
		progressArray=[]
		for progress in progressDic:
			if progress!='load':
				progressArray.append(_(progress)+': '+str(int(progressDic[progress]))+'%')
		print(','.join(progressArray),end="\r")
		time.sleep(0.1)
		for key in actionList:
			progressDic=store.get_progress(key)
			if key in progressDic:
				if progressDic[key]==100 and not actionList[key]:
					progressDic=store.get_progress(key)
					progressArray=[]
					for progress in progressDic:
						if progress!='load':
							progressArray.append(_(progress)+': '+str(progressDic[progress])+'%')
					print(','.join(progressArray))
					print (CURSOR_UP + ERASE_LINE)
					actionList[key]=print_results(key)
#	print_results('random')

def process_Args(args):
	parser=argparse.ArgumentParser(description=(u'Lliurex Store.'))
	parser.add_argument('-s','--search',metavar='Name',nargs='?',help=(_(u"Search a package")))
	parser.add_argument('-v','--view',metavar='Name',nargs='?',help=(_(u"Show all info from a package")))
	parser.add_argument('-i','--install',metavar='Package',help=(_(u"Install a package")))
	parser.add_argument('-r','--remove',metavar='Package',help=(_(u"Remove a package")))
#	parser.add_argument('--random',metavar='Results',help=(_(u"List random packages")))
#	parser.add_argument('--debug',action='store_true',help=(_(u"Prints debug information")))
	parser.add_argument('--appimage',action='store_true',help=(_(u"Load appimage catalog")))
	parser.add_argument('--snap',action='store_true',help=(_(u"Load snap catalog")))
#	parser.add_argument('--list',metavar='list',nargs='?',help=(_(u"List category")))

	args=parser.parse_args()
	return args

main()
