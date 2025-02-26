# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies and contributors
# License: MIT. See LICENSE

import json

import frappe
from frappe.utils.safe_exec import safe_exec
from frappe.model.document import Document

class SystemConsole(Document):
	def run(self):
		frappe.only_for('System Manager')
		try:
			frappe.debug_log = []
			safe_exec(self.console)
			self.output = '\n'.join(frappe.debug_log)
		except: # noqa: E722
			self.output = frappe.get_traceback()

		if self.commit:
			frappe.db.commit()
		else:
			frappe.db.rollback()

		frappe.get_doc(dict(
			doctype='Console Log',
			script=self.console,
			output=self.output)).insert()
		frappe.db.commit()

@frappe.whitelist()
def execute_code(doc):
	console = frappe.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()

@frappe.whitelist()
def show_processlist():
	frappe.only_for('System Manager')
	return frappe.db.sql('show processlist', as_dict=1)
