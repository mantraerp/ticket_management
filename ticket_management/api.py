"""
Ticket API  (ticket_management/api.py)

The "Raise a Ticket" form that every ERP portal shows (mantra/templates/includes/raise_ticket_check.html)
calls this module by default. The portals run on the same site, so tickets are created as the
logged-in user:

    get_options()      Module / Type choices (the enabled Ticket Module / Ticket Type records,
                       managed from the desk) and the attachment limits
    submit_ticket()    creates the Ticket and saves the uploaded files on it as private files
    get_my_tickets()   the user's own Tickets, newest first

My Ticket.before_insert fills in who raised it (User / Employee) and where from (IP, page, browser).
My Ticket permissions: the "All" role may create Tickets and read its own, so everything here runs
with the user's own permissions; only the attachments are saved on their behalf.
"""

import frappe
from frappe.utils import escape_html

TICKET_DOCTYPE = "My Ticket"
MAX_ATTACHMENTS = 10
MAX_FILE_MB = 10
MAX_TOTAL_MB = 25
# Tickets a user may raise in an hour (stops accidental repeats and floods)
MAX_TICKETS_PER_HOUR = 10
# Tickets returned by get_my_tickets
MY_TICKETS_LIMIT = 50


def _choices(fieldname):
	"""Enabled records of the master a My Ticket Link field points to (Ticket Module / Ticket Type)."""
	master = frappe.get_meta(TICKET_DOCTYPE).get_field(fieldname).options
	return frappe.get_all(master, filters={"enabled": 1}, pluck="name", order_by="creation asc")


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw("Please log in to raise a ticket.", frappe.PermissionError)


@frappe.whitelist()
def get_options():
	"""Choices for the form's Module and Type fields, and the attachment limits."""
	_require_login()
	return {
		"modules": _choices("module"),
		"types": _choices("issue_type"),
		"max_attachments": MAX_ATTACHMENTS,
		"max_file_mb": MAX_FILE_MB,
		"max_total_mb": MAX_TOTAL_MB,
	}


@frappe.whitelist(methods=["POST"])
def submit_ticket(subject=None, module=None, issue_type=None, description=None, steps=None, page_url=None):
	"""Create a Ticket from the portal form. Attachments arrive as multipart files named "attachments"."""
	_require_login()

	subject = (subject or "").strip()
	description = (description or "").strip()
	module = (module or "").strip()
	issue_type = (issue_type or "").strip()
	if not subject:
		frappe.throw("Subject is required.")
	if len(subject) > 140:
		frappe.throw("Subject can be at most 140 characters.")
	if module not in _choices("module"):
		frappe.throw("Please choose a Module.")
	if issue_type not in _choices("issue_type"):
		frappe.throw("Please choose a Type.")
	if not description:
		frappe.throw("Description is required.")

	_check_rate(frappe.session.user)
	attachments = _read_attachments()  # checked before anything is saved

	ticket = frappe.get_doc(
		{
			"doctype": TICKET_DOCTYPE,
			"subject": subject,
			"module": module,
			"issue_type": issue_type,
			"description": description,
			"steps": (steps or "").strip(),
			"page_url": (page_url or "").strip()[:1000],
		}
	)
	ticket.insert()

	# The raiser may create Tickets but not edit them, so the files are attached on their behalf
	for f in attachments:
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f["fname"],
				"content": f["fcontent"],
				"attached_to_doctype": TICKET_DOCTYPE,
				"attached_to_name": ticket.name,
				"is_private": 1,
			}
		).insert(ignore_permissions=True)

	count = len(attachments)
	return {
		"reference": ticket.name,
		"title": "Ticket created",
		"note": f"Your ticket {ticket.name} has been raised"
		+ (f" with {count} attachment{'' if count == 1 else 's'}" if count else "")
		+ ". The support team will follow it up.",
	}


@frappe.whitelist()
def get_my_tickets():
	"""The logged-in user's own Tickets, newest first."""
	_require_login()
	return frappe.get_list(
		TICKET_DOCTYPE,
		fields=["name", "subject", "module", "issue_type", "status", "raised_on"],
		filters={"raised_by": frappe.session.user},
		order_by="creation desc",
		page_length=MY_TICKETS_LIMIT,
	)


def _check_rate(user):
	key = f"ticket_management:create:{user}"
	count = frappe.cache().incrby(key, 1)
	if count == 1:
		frappe.cache().expire(key, 3600)
	if count > MAX_TICKETS_PER_HOUR:
		frappe.throw("You have raised many tickets in the last hour. Please try again later.")


def _read_attachments():
	"""[{fname, fcontent}] from the request, within the count and size limits."""
	files = frappe.request.files.getlist("attachments") if frappe.request and frappe.request.files else []
	files = [f for f in files if f and f.filename]
	if len(files) > MAX_ATTACHMENTS:
		frappe.throw(f"You can attach up to {MAX_ATTACHMENTS} files.")
	out, total = [], 0
	for f in files:
		content = f.read()
		if len(content) > MAX_FILE_MB * 1024 * 1024:
			frappe.throw(f'"{escape_html(f.filename)}" is larger than {MAX_FILE_MB} MB.')
		total += len(content)
		if total > MAX_TOTAL_MB * 1024 * 1024:
			frappe.throw(f"Attachments together can be at most {MAX_TOTAL_MB} MB.")
		out.append({"fname": f.filename, "fcontent": content})
	return out
