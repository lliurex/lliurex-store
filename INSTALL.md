## Instalation

There're available packages for LliureX and other Ubuntu-related distributions at LliureX own repositories and LliureX ppa for both xenial and bionic (beta).
- [ppa-xenial](https://launchpad.net/~llxdev/+archive/ubuntu/xenial)
- [ppa-bionic](https://launchpad.net/~llxdev/+archive/ubuntu/bionic)

Once the repositories or ppa are added:

	sudo apt-get update
	sudo apt-get install lliurex-store

## Manual installation

If you want you could install the store manually, there's no automated process.

### Check requeriments

The store needs all these libs:
 - python3-html2text
 - appstream
 - libappstream4
 - gir1.2-appstreamglib-1.0
 - packagekit
 - libpackagekit-glib2
 - gir1.2-packagekitglib-1.0
 - python3-bs4

If you wish snap support then also:
 - libsnapd-glib1
 - gir1.2-snapd-1

Zmd is enabled only if LliureX's N4d is present

### Install the python libs
Simply run setup.py from root folder

	python3 setup.py

### Copy the executables and needed files

- lliurex-store-cli:

	cp lliurex-store-cli/usr/share/lliurex-store /usr/share -r
	ln -s /usr/share/lliurex-store/lliurex-store-cli.py /usr/bin/lliurex-store-cli

- lliurex-store-gui:

	cp lliurex-store-gui/usr/share/lliurex-store-gui /usr/share -r
	ln -s /usr/share//lliurex-store/lliurex-store-gui/lliurex-store.py /usr/bin/lliurex-store

- desktop file:

	cp lliurex-store-gui/usr/share/applications/* /usr/share/applications/

- mate users:

	cp lliurex-store-gui/usr/share/mate-background-properties/* /usr/share/mate-background-properties/ 

