# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import frappe, os, json
from frappe.modules import get_module_path, scrub_dt_dn
from frappe.utils import get_datetime_str
from frappe.model.base_document import get_controller

ignore_values = {
	"Report": ["disabled", "prepared_report", "add_total_row"],
	"Print Format": ["disabled"],
	"Notification": ["enabled"],
	"Print Style": ["disabled"],
	"Module Onboarding": ['is_complete'],
	"Onboarding Step": ['is_complete', 'is_skipped']
}

ignore_doctypes = [""]

def import_files(module, dt=None, dn=None, force=False, pre_process=None, reset_permissions=False):
	if type(module) is list:
		out = []
		for m in module:
			out.append(import_file(m[0], m[1], m[2], force=force, pre_process=pre_process,
				reset_permissions=reset_permissions))
		return out
	else:
		return import_file(module, dt, dn, force=force, pre_process=pre_process,
			reset_permissions=reset_permissions)

def import_file(module, dt, dn, force=False, pre_process=None, reset_permissions=False):
	"""Sync a file from txt if modifed, return false if not updated"""
	path = get_file_path(module, dt, dn)
	ret = import_file_by_path(path, force, pre_process=pre_process, reset_permissions=reset_permissions)
	return ret

def get_file_path(module, dt, dn):
	dt, dn = scrub_dt_dn(dt, dn)

	path = os.path.join(get_module_path(module),
		os.path.join(dt, dn, dn + ".json"))

	return path

def import_file_by_path(path, force=False, data_import=False, pre_process=None, ignore_version=None,
		reset_permissions=False, for_sync=False):
	try:
		docs = read_doc_from_file(path)
	except IOError:
		print (path + " missing")
		return

	if docs:
		if not isinstance(docs, list):
			docs = [docs]

		for doc in docs:
			if not force and not is_changed(doc):
				return False

			original_modified = doc.get("modified")

			import_doc(doc, force=force, data_import=data_import, pre_process=pre_process,
				ignore_version=ignore_version, reset_permissions=reset_permissions, path=path)

			if original_modified:
				update_modified(original_modified, doc)

	return True

def is_changed(doc):
	# check if timestamps match
	db_modified = frappe.db.get_value(doc['doctype'], doc['name'], 'modified')
	if db_modified and doc.get('modified')==get_datetime_str(db_modified):
		return False
	return True

def read_doc_from_file(path):
	doc = None
	if os.path.exists(path):
		with open(path, 'r') as f:
			try:
				doc = json.loads(f.read())
			except ValueError:
				print("bad json: {0}".format(path))
				raise
	else:
		raise IOError('%s missing' % path)

	return doc

def update_modified(original_modified, doc):
	# since there is a new timestamp on the file, update timestamp in
	if doc["doctype"] == doc["name"] and doc["name"]!="DocType":
		frappe.db.sql("""update tabSingles set value=%s where field="modified" and doctype=%s""",
			(original_modified, doc["name"]))
	else:
		frappe.db.sql("update `tab%s` set modified=%s where name=%s" % (doc['doctype'],
			'%s', '%s'), (original_modified, doc['name']))

def import_doc(docdict, force=False, data_import=False, pre_process=None,
		ignore_version=None, reset_permissions=False, path=None):
	frappe.flags.in_import = True
	docdict["__islocal"] = 1

	controller = get_controller(docdict['doctype'])
	if controller and hasattr(controller, 'prepare_for_import') and callable(getattr(controller, 'prepare_for_import')):
		controller.prepare_for_import(docdict)

	doc = frappe.get_doc(docdict)

	reset_tree_properties(doc)
	load_code_properties(doc, path)

	doc.run_method("before_import")

	doc.flags.ignore_version = ignore_version
	if pre_process:
		pre_process(doc)

	if frappe.db.exists(doc.doctype, doc.name):
		delete_old_doc(doc, reset_permissions)

	doc.flags.ignore_links = True
	if not data_import:
		doc.flags.ignore_validate = True
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True

	doc.insert()

	frappe.flags.in_import = False

	return doc

def load_code_properties(doc, path):
	'''Load code files stored in separate files with extensions'''
	if path:
		if hasattr(doc, 'get_code_fields'):
			dirname, filename = os.path.split(path)
			for key, extn in doc.get_code_fields().items():
				codefile = os.path.join(dirname, filename.split('.')[0]+'.'+extn)
				if os.path.exists(codefile):
					with open(codefile,'r') as txtfile:
						doc.set(key, txtfile.read())


def delete_old_doc(doc, reset_permissions):
	ignore = []
	old_doc = frappe.get_doc(doc.doctype, doc.name)

	if doc.doctype in ignore_values:
		# update ignore values
		for key in ignore_values.get(doc.doctype) or []:
			doc.set(key, old_doc.get(key))

	# update ignored docs into new doc
	for df in doc.meta.get_table_fields():
		if df.options in ignore_doctypes and not reset_permissions:
			doc.set(df.fieldname, [])
			ignore.append(df.options)

	# delete old
	frappe.delete_doc(doc.doctype, doc.name, force=1, ignore_doctypes=ignore, for_reload=True)

	doc.flags.ignore_children_type = ignore

def reset_tree_properties(doc):
	# Note on Tree DocTypes:
	# The tree structure is maintained in the database via the fields "lft" and
	# "rgt". They are automatically set and kept up-to-date. Importing them
	# would destroy any existing tree structure.
	if getattr(doc.meta, 'is_tree', None) and any([doc.lft, doc.rgt]):
		print('Ignoring values of `lft` and `rgt` for {} "{}"'.format(doc.doctype, doc.name))
		doc.lft = None
		doc.rgt = None
