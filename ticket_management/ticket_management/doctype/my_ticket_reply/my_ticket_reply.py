# Copyright (c) 2026, Ravi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

TICKET_DOCTYPE = "My Ticket"


class MyTicketReply(Document):
	def before_insert(self):
		self.replied_by = frappe.session.user
		self.replied_by_name = frappe.db.get_value("User", self.replied_by, "full_name") or self.replied_by

	def validate(self):
		if not frappe.has_permission(TICKET_DOCTYPE, "read", self.ticket):
			frappe.throw(f"You cannot reply on ticket {self.ticket}.", frappe.PermissionError)
		if not frappe.utils.strip_html(self.reply or "").strip():
			frappe.throw("Reply is required.")


def _is_support(user):
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def get_permission_query_conditions(user=None):
	"""Other users see only replies on the tickets they raised, and their own replies."""
	user = user or frappe.session.user
	if _is_support(user):
		return ""
	user = frappe.db.escape(user)
	return (
		f"(`tabMy Ticket Reply`.owner = {user} or `tabMy Ticket Reply`.ticket in "
		f"(select name from `tabMy Ticket` where owner = {user} or raised_by = {user}))"
	)


def has_permission(doc, ptype=None, user=None):
	user = user or frappe.session.user
	if _is_support(user) or ptype == "create" or doc.owner == user:
		return True
	raiser = frappe.db.get_value(TICKET_DOCTYPE, doc.ticket, ["owner", "raised_by"], as_dict=True)
	return bool(raiser) and user in (raiser.owner, raiser.raised_by)
