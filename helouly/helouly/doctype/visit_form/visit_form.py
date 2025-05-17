# Copyright (c) 2024, Smart Solution and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class VisitForm(Document):
	pass

@frappe.whitelist()
def create_visit_from_lead(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.lead_name = source.name  # Map the Lead to Visit Form field
        # Add additional mappings as necessary

    return frappe.model.mapper.get_mapped_doc(
        "Lead",
        source_name,
        {
            "Lead": {
                "doctype": "Visit Form",
                "field_map": {
                     "sales_partner": "partner_name", 
                }
            }
        },
        target_doc,
        set_missing_values
    )

@frappe.whitelist()
def create_visit_from_opportunity(source_name, target_doc=None):
    def set_missing_values(source, target):
        # Get the document name (ID) of the Lead linked in the Opportunity's lead_name field
        lead_doc_name = frappe.db.get_value("Lead", {"lead_name": source.lead_name}, "name")

        # Set the Lead's document name in Visit Form's lead_name field
        target.lead_name = lead_doc_name
        target.opportunity = source.name  # Set the Opportunity's document name in Visit Form's opportunity field

    return frappe.model.mapper.get_mapped_doc(
        "Opportunity",
        source_name,
        {
            "Opportunity": {
                "doctype": "Visit Form",
                "field_map": {
                    "sales_partner": "partner_name",
                }
            }
        },
        target_doc,
        set_missing_values
    )
