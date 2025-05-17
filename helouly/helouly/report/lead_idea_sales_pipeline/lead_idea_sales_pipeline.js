// Copyright (c) 2023, Smart Solution and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Lead Idea Sales Pipeline"] = {
	"filters": [



{
			"fieldname":"status",
			"label": __("Status"),
			"fieldtype": "Select",
			options: [
				{ "value": "Lead", "label": __("Lead") },
				{ "value": "Open", "label": __("Open") },
				{ "value": "Replied", "label": __("Replied") },
				{ "value": "Opportunity", "label": __("Opportunity") },
				{ "value": "Quotation", "label": __("Quotation") },
				{ "value": "Lost Quotation", "label": __("Lost Quotation") },
				{ "value": "Interested", "label": __("Interested") },
				{ "value": "Converted", "label": __("Converted") },
				{ "value": "Do Not Contact", "label": __("Do Not Contact") },
			],
		},


{
			fieldname: "team_leader",
			label: __("Team Leader"),
			fieldtype: "Link",
			options: "Sales Person",
	
		},


                {
			fieldname: "sales_partner",
			label: __("Sales Partner"),
			fieldtype: "Link",
			options: "Sales Partner",
	
		},

{
			fieldname: "industry",
			label: __("Sector"),
			fieldtype: "Link",
                        options: "Industry Type",

				
		},


	]
};
