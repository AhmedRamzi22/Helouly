
frappe.ui.form.on("Lead", {
    setup: function(frm) {
        frm.set_query("territory", function () {
            return {
                filters: {
                    is_group: ["!=", 1]
                }
            };
        });
    },
    
	refresh: function(frm) {
        frm.add_custom_button(__('Visit Form'), function() {
            frappe.model.open_mapped_doc({
                method: "helouly.helouly.doctype.visit_form.visit_form.create_visit_from_lead",
                frm: frm
            });
        }, __('Create'));
    }

});

frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        setTimeout(() => {
           frm.remove_custom_button('Opportunity', 'Create'); 
        }, 10);
        if (!frm.is_new() && frm.doc.__onload && !frm.doc.__onload.is_customer) {
            setTimeout(() => {
    			frm.add_custom_button(
    				__("Opportunity"),
    				function () {
    					frm.trigger("custom_make_opportunity");
    				},
    				__("Create")
    			);
            }, 50);
        }
    },
	custom_make_opportunity: async function (frm) {
		let existing_prospect = (
			await frappe.db.get_value(
				"Prospect Lead",
				{
					lead: frm.doc.name,
				},
				"name",
				null,
				"Prospect"
			)
		).message.name;

		if (!existing_prospect) {
			var fields = [
				{
					label: "Create Prospect",
					fieldname: "create_prospect",
					fieldtype: "Check",
					default: 0,
				},
				{
					label: "Prospect Name",
					fieldname: "prospect_name",
					fieldtype: "Data",
					default: frm.doc.company_name,
					depends_on: "create_prospect",
				},
			];
		}
		let existing_contact = (
			await frappe.db.get_value(
				"Contact",
				{
					first_name: frm.doc.first_name || frm.doc.lead_name,
					last_name: frm.doc.last_name,
				},
				"name"
			)
		).message.name;

		if (!existing_contact) {
			fields.push({
				label: "Create Contact",
				fieldname: "create_contact",
				fieldtype: "Check",
				default: "1",
			});
		}

		if (fields) {
			var d = new frappe.ui.Dialog({
				title: __("Create Opportunity"),
				fields: fields,
				primary_action: function () {
					var data = d.get_values();
					frappe.call({
						method: "create_prospect_and_contact",
						doc: frm.doc,
						args: {
							data: data,
						},
						freeze: true,
						callback: function (r) {
							if (!r.exc) {
								frappe.model.open_mapped_doc({
									method: "erpnext.crm.doctype.lead.lead.make_opportunity",
									frm: frm,
								});
							}
							d.hide();
						},
					});
				},
				primary_action_label: __("Create"),
			});
			d.show();
		} else {
			frappe.model.open_mapped_doc({
				method: "erpnext.crm.doctype.lead.lead.make_opportunity",
				frm: frm,
			});
		}
	},
});
