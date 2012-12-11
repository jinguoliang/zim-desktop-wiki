# -*- coding: utf-8 -*-

# Copyright 2008 Jaap Karssenberg <jaap.karssenberg@gmail.com>

'''Plugin to serve as work-around for the lack of printing support'''

import gtk

from zim.fs import TmpFile
from zim.plugins import PluginClass
import zim.templates
from zim.exporter import StaticLinker


ui_xml = '''
<ui>
	<menubar name='menubar'>
		<menu action='file_menu'>
			<placeholder name='print_actions'>
				<menuitem action='print_to_browser'/>
			</placeholder>
		</menu>
	</menubar>
</ui>
'''

ui_actions = (
	# name, stock id, label, accelerator, tooltip, readonly
	('print_to_browser', 'gtk-print', _('_Print to Browser'), '<ctrl>P', 'Printto browser', True), # T: menu item

)

class PrintToBrowserPlugin(PluginClass):

	plugin_info = {
		'name': _('Print to Browser'), # T: plugin name
		'description': _('''\
This plugin provides a workaround for the lack of
printing support in zim. It exports the current page
to html and opens a browser. Assuming the browser
does have printing support this will get your
data to the printer in two steps.

This is a core plugin shipping with zim.
'''), # T: plugin description
		'author': 'Jaap Karssenberg',
		'help': 'Plugins:Print to Browser'
	}

	def __init__(self, ui):
		PluginClass.__init__(self, ui)
		if self.ui.ui_type == 'gtk':
			self.ui.add_actions(ui_actions, self)
			self.ui.add_ui(ui_xml, self)

	def print_to_browser(self, page=None):
		file = self.print_to_file(page)
		self.ui.open_url('file://%s' % file)
			# Try to force web browser here - otherwise it goes to the
			# file browser which can have unexpected results

	def print_to_file(self, page=None):
		if not page:
			page = self.ui.page

		# FIXME - HACK - dump and parse as wiki first to work
		# around glitches in pageview parsetree dumper
		# main visibility when copy pasting bullet lists
		# Same hack in gui clipboard code
		from zim.notebook import Path, Page
		from zim.formats import get_format
		parsetree = page.get_parsetree()
		dumper = get_format('wiki').Dumper()
		text = ''.join( dumper.dump(parsetree) ).encode('utf-8')
		parser = get_format('wiki').Parser()
		parsetree = parser.parse(text)
		page = Page(Path(page.name), parsetree=parsetree)
		#--

		file = TmpFile('print-to-browser.html', persistent=True, unique=False)
		template = zim.templates.get_template('html', 'Print')
		template.set_linker(StaticLinker('html', self.ui.notebook, page))
		html = template.process(self.ui.notebook, page)
		file.writelines(html)
		return file

	def do_decorate_window(self, window):
		# Add a print button to the tasklist dialog
		if not window.__class__.__name__ == 'TaskListDialog':
			return

		buttons = [b for b in window.action_area.get_children()
			if not window.action_area.child_get_property(b, 'secondary')]
		close_button = buttons[0] # HACK: not sure this order fixed

		button = gtk.Button(stock='gtk-print')
		window.action_area.pack_end(button, False)
		button.connect('clicked', self.on_print_tasklist, window.task_list)

		window.action_area.reorder_child(close_button, -1)

	def on_print_tasklist(self, o, task_list):
		html = task_list.get_visible_data_as_html()

		file = TmpFile('print-to-browser.html', persistent=True, unique=False)
		file.write(html)
		self.ui.open_url('file://%s' % file)
			# Try to force web browser here - otherwise it goes to the
			# file browser which can have unexpected results
