// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.listview_settings["Department Request Form"] = {
	add_fields: ["status"],
	has_indicator_for_draft: 1,
	get_indicator: function (doc) {
		if (doc.request_status == "Resolved") {
			return [__(doc.request_status), "green", "request_status,=," + doc.request_status];
		} else if (doc.request_status == "Open") {
			return [__(doc.request_status), "orange", "request_status,=," + doc.request_status];
		} else if (doc.request_status == "Overdue") {
			return [__(doc.request_status), "red", "request_status,=," + doc.request_status];
		} else if (doc.request_status == "Closed") {
			return [__(doc.request_status), "yellow", "request_status,=," + doc.request_status];
		}else if (doc.request_status == "Under Processing") {
			return [__(doc.request_status), "grey", "request_status,=," + doc.request_status];
		}
        
	},
};
