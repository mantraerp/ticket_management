import frappe

from ticket_management.install import create_default_masters


def execute():
	"""Create the default masters, plus any Module / Type an existing ticket already uses."""
	create_default_masters()
	for fieldname, doctype, field in (
		("module", "Ticket Module", "module_name"),
		("issue_type", "Ticket Type", "type_name"),
	):
		for value in frappe.get_all("My Ticket", pluck=fieldname, distinct=True):
			if value and not frappe.db.exists(doctype, value):
				frappe.get_doc({"doctype": doctype, field: value, "enabled": 1}).insert(ignore_permissions=True)
