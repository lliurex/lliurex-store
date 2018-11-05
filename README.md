# Lliurex Store
<p>Software store for Lliurex.</p>
<p>
Offers support for Lliurex's zomandos, snaps, appimage and software repositories.<br>
It can be also be installed on a non-Lliurex system and it shall enable or disable plugins if any of them isn't supported on the base system</p>
## Lliurex Store plugin system
<p>
Plugins must provide one register method and return a dictionary with "data" and "status" keys.<br>
The basic structure of a plugin is provided at the "example.py" plugin.
</p>
### Available public methods
<ul>
<li>
<b>execute_action(str(action_name))</b>
<p>
Executes "action" in a thread. When action is finished it will publish the result through the get_results method.
</p>
</li>
<li>
<b>get_progress(str(action_name) or None)</b>
<p>
Gets the current progress of a running action or of all actions launched
</p>
</li>
<li>
<b>get_result(str(action_name))</b>
<p>
Gets the result of action. This function will join the action till it's finished
</p>
</li>
<li>
<b>get_status(str(action_name) or None)</b>
<p>
Gets the return status of an action
</p>
</li>
<li>
<b>set_debug(bool(debug))</b>
<p>
Enables or disables debug
</p>
</li>
</ul>
