
# Copyright 2008-2018 Jaap Karssenberg <jaap.karssenberg@gmail.com>

from gi.repository import Gtk
from zim.gui.widgets import Dialog, get_window, InputForm

notebook_properties = (
	('name', 'string', _('Name')), # T: label for properties dialog
	('interwiki', 'string', _('Interwiki Keyword'), lambda v: not v or is_interwiki_keyword_re.search(v)), # T: label for properties dialog
	('home', 'page', _('Home Page')), # T: label for properties dialog
	('icon', 'image', _('Icon')), # T: label for properties dialog
	('document_root', 'dir', _('Document Root')), # T: label for properties dialog
	('profile', 'string', _('Profile')), # T: label for properties dialog
	# 'shared' property is not shown in properties anymore
)


class PropertiesDialog(Dialog):

	def __init__(self, parent, config, notebook):
		Dialog.__init__(self, parent, _('Properties'), help='Help:Properties') # T: Dialog title
		self.notebook = notebook
		self.config = config

		stack = Gtk.Stack()
		sidebar = Gtk.StackSidebar()
		sidebar.set_stack(stack)

		hbox = Gtk.Box()
		hbox.add(sidebar)
		hbox.add(stack)
		self.vbox.add(hbox)

		self.form = InputForm(
			inputs=notebook_properties,
			values=notebook.config['Notebook']
		)
		self.form.widgets['icon'].set_use_relative_paths(self.notebook)
		if self.notebook.readonly:
			for widget in list(self.form.widgets.values()):
				widget.set_sensitive(False)
		stack.add_titled(self.form, 'notebook', _('Notebook'))

		self.plugin_forms = {}
		plugins = get_window(parent).__pluginmanager__ # XXX
		for name in plugins:
			plugin = plugins[name]
			if plugin.plugin_notebook_properties:
				key = plugin.config_key
				form = InputForm(
					inputs=plugin.form_fields(plugin.plugin_notebook_properties),
					values=notebook.config[key]
				)
				self.plugin_forms[key] = form
				if self.notebook.readonly:
					for widget in list(form.widgets.values()):
						widget.set_sensitive(False)

				box = Gtk.VBox()
				box.pack_start(form, False, False, 0)
				stack.add_titled(box, name, plugin.plugin_info['name'])

	def do_response_ok(self):
		if not self.notebook.readonly:
			properties = self.form.copy()

			# XXX this should be part of notebook.save_properties
			# which means notebook should also own a ref to the ConfigManager
			if 'profile' in properties and properties['profile'] != self.notebook.profile:
				assert isinstance(properties['profile'], (str, type(None)))
				self.config.set_profile(properties['profile'])

			self.notebook.save_properties(**properties)

			for key, form in self.plugin_forms.items():
				self.notebook.config[key].update(form)

		return True

## TODO: put a number of properties in an expander with a lable "Advanced"
