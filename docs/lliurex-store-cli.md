# lliurex-store-cli(1)

## SYNOPSYS
	lliurex-store-cli [OPTIONS] package_name [--appimage] [--snap]

## DESCRIPTION
	Manage packages from the Lliurex Store.
	
	Mandatory arguments to long options are mandatory for short options too.

	-s, --search [name]
		Search *name* in the Lliurex Store. Name could be a package name, a descriptive string or anything else related with a program.

	-v, --view [package]
		Shows extended information for package. Package must be a full package name.

	-i, --install [package]
		Installs package. Package must be a full package name.

	-r, --remove [package]
		Removes package. Package must be a full package name.

	--appimage
		Enables appimage plugin. Appimages due to its nature are downloaded to $HOME/.local/bin and installed per-user

	--snap
		Enables snap plugin

	--update
		Updates the cache database. For including appimage and snaps the corresponding arguments must be passed too.

	In order to work with appimages or snaps is mandatory to enable their respective plugins. Install, view and remove options needed the full package name as returned by the search. Search can search by name or metainformation of a package thus you can search for "photo" to retrieve all the available applications related to photography (image processing, image cataloguing...etc..)

## EXAMPLES
	* Search for a multimedia player:
	lliurex-store-cli -s player

	* Search for a CAD application in all sources:
	lliurex-store-cli -s CAD --appimage --snap

	* View information for package firefox-esr:
	lliurex-store-cli -v firefox-esr

	* View information for appimage package subsurface.appimage:
	lliurex-store-cli -v subsurface.appimage --appimage`

	* Install firefox from snap:
	lliurex-store-cli -i firefox.snap --snap

	* Remove epiphany-browser:
	lliurex-store-cli -r epiphany-browser

	* Remove subsurface appimage:
	lliurex-store-cli -r subsurface.appimage --appimage

## REPORTING BUGS
	Lliurex Github: https://github.com/lliurex/lliurex-store/issues

## SEE ALSO
	Snapcraft: https://snapcraft.io
	Appimage: https://appimage.org
