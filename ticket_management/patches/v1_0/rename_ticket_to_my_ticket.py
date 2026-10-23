import frappe


def execute():
	"""Rename the Ticket DocType to My Ticket on sites that already have it, keeping its records."""
	if not frappe.db.exists("DocType", "Ticket") or frappe.db.exists("DocType", "My Ticket"):
		return
	if frappe.db.get_value("DocType", "Ticket", "module") != "Ticket Management":
		return
	frappe.rename_doc("DocType", "Ticket", "My Ticket", force=True)
