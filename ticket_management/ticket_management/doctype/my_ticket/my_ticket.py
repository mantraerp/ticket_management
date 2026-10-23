# Copyright (c) 2026, Ravi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MyTicket(Document):
	def before_insert(self):
		self.set_raised_by()
		self.set_source()

	def set_source(self):
		"""Where the ticket came from: session user, IP address, page URL and browser."""
		self.session_user = frappe.session.user
		self.ip_address = getattr(frappe.local, "request_ip", None)
		if frappe.request:
			# The portal popup sends page_url; fall back to the page that made the request
			self.page_url = self.page_url or frappe.request.headers.get("Referer")
			self.browser = self.browser or frappe.request.headers.get("User-Agent")

	def validate(self):
		self.validate_enabled("module", "Ticket Module")
		self.validate_enabled("issue_type", "Ticket Type")
		self.subject = (self.subject or "").strip()
		self.description = (self.description or "").strip()
		if not self.subject:
			frappe.throw("Subject is required.")
		if not self.description:
			frappe.throw("Description is required.")

	def validate_enabled(self, fieldname, master):
		"""A new or changed Module / Type must be enabled; old tickets keep a value disabled later."""
		value = self.get(fieldname)
		if value and self.has_value_changed(fieldname) and not frappe.db.get_value(master, value, "enabled"):
			frappe.throw(f"{master} {value} is disabled.")

	def set_raised_by(self):
		"""Who raised the ticket: User record, plus their Employee record when there is one."""
		user = self.raised_by or frappe.session.user
		account = (
			frappe.db.get_value("User", user, ["full_name", "email", "mobile_no", "phone"], as_dict=True)
			or frappe._dict()
		)
		employee = frappe._dict()
		if frappe.db.exists("DocType", "Employee"):
			employee = (
				frappe.db.get_value(
					"Employee",
					{"user_id": user, "status": ["!=", "Left"]},
					["name", "employee_name", "designation", "department", "company", "cell_number", "company_email"],
					as_dict=True,
				)
				or frappe._dict()
			)

		self.raised_by = user
		self.full_name = employee.employee_name or account.full_name or user
		self.email = employee.company_email or account.email or user
		self.mobile = employee.cell_number or account.mobile_no or account.phone
		self.employee = employee.name
		self.designation = employee.designation
		self.department = employee.department
		self.company = employee.company or frappe.defaults.get_global_default("company")
