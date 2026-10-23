import frappe

# Starting records for the Ticket Module and Ticket Type masters (the choices the portal form had)
DEFAULT_MODULES = [
	"Buying",
	"Selling",
	"Accounting",
	"Stock",
	"Manufacturing",
	"Quality",
	"Projects / Tasks",
	"HR & Payroll",
	"Assets",
	"CRM",
	"Employee Portal",
	"Servico",
	"Payment",
	"Dispatch",
	"Other",
]
DEFAULT_TYPES = ["Permission", "Data issue", "Other"]


def after_install():
	create_default_masters()


def create_default_masters():
	"""Add the default Modules and Types that are missing; existing records are left as they are."""
	for doctype, field, values in (
		("Ticket Module", "module_name", DEFAULT_MODULES),
		("Ticket Type", "type_name", DEFAULT_TYPES),
	):
		for value in values:
			if not frappe.db.exists(doctype, value):
				frappe.get_doc({"doctype": doctype, field: value, "enabled": 1}).insert(ignore_permissions=True)
