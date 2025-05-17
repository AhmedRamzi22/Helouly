// Copyright (c) 2023, smart and contributors
// For license information, please see license.txt

frappe.ui.form.on('Opportunity', {

    setup: function(frm) {
        // Fetch sales_partner from the Lead linked to the Opportunity
        frappe.db.get_value('Lead', frm.doc.party_type, 'sales_partner')
            .then(r => {
                frappe.set_value("sales_partner", r.message.sales_partner);
            });
    },

    refresh: function(frm) {
        console.log("refreshed")
        // Add button to create 'Operation Request' with pre-filled values
        frm.add_custom_button(__('Operation Request'), () => {
            frappe.new_doc('Operation Request', {
                "party": frm.doc.opportunity_from,
                "party_type": frm.doc.party_name,
                "opportunity": frm.docname,
                "sales_partner": frm.doc.sales_partner
            });
        }, __('Create'));

        // Add button to create 'Visit Form' with a custom method
        frm.add_custom_button(__('Visit Form'), function() {
            frappe.model.open_mapped_doc({
                method: "helouly.helouly.doctype.visit_form.visit_form.create_visit_from_opportunity",
                frm: frm
            });
        }, __('Create'));
    }
});
