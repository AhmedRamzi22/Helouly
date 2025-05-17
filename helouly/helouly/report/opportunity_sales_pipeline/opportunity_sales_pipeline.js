// Copyright (c) 2023, Smart Solution and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Opportunity Sales Pipeline"] = {
	"filters": [

{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date"
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
			fieldname: "opportunity_product_type",
			label: __("Opportunity Product Type"),
			fieldtype: "Link",
			options: "Opportunity Product Type",
	
		},


{
			fieldname: "opportunity_product",
			label: __("Opportunity Product"),
			fieldtype: "Link",
			options: "Opportunity Product",
	
		},


{
			fieldname: "sales_stage",
			label: __("Sales Stage"),
			fieldtype: "Link",
			options: "Sales Stage",
	
		},

{
			fieldname: "industry",
			label: __("Sector"),
			fieldtype: "Link",
			options: "Industry Type",
	
		},




			
	]
};
