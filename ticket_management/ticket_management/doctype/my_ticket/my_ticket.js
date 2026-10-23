// Copyright (c) 2026, Ravi and contributors
// For license information, please see license.txt

frappe.ui.form.on("My Ticket", {
	setup(frm) {
		frm.set_query("module", () => ({ filters: { enabled: 1 } }));
		frm.set_query("issue_type", () => ({ filters: { enabled: 1 } }));
	},
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Reply"), () => {
			frappe.new_doc("My Ticket Reply", { ticket: frm.doc.name });
		});
	},
});
