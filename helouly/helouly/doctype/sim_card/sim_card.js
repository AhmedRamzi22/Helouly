// Copyright (c) 2023, Smart Solution and contributors
// For license information, please see license.txt

frappe.ui.form.on('SIM Card', {
	refresh: function(frm) {
		frm.events.create_sim_issue(frm)
	},
	create_sim_issue:function(frm){
		if (frm.doc.docstatus !=1 ){
			return
		}
		frm.add_custom_button('SIM Issue', () => {
			
		}, 'Create');


	}
});
