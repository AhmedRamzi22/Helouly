import frappe


@frappe.whitelist()
def get_voice_consumption(operation_contract):
    voices = []
    invoices_contracts = frappe.db.get_list(
        "Invoices Contract",
        filters={
            "parent": operation_contract,
            "parenttype": "Operation Contract",
            "voiced": 1,
            "status": ["!=", "Submitted"],
        },
        fields=["name", "invoice_due_date"],
    )

    for invoice in invoices_contracts:
        voice_log = frappe.db.get_value(
            "Voice Consumption Log", {"invoices_schedual_row_name": invoice["name"]}, ["name"]
        )
        invoice_log, rate = frappe.db.get_value(
            "Invoice Log Items",
            {
                "parenttype": "Invoice Log",
                "row_name": voice_log,
                "voice": 1,
            },
            ["name", "rate"],
        )

        voices.append(
            {
                "date": invoice["invoice_due_date"],
                "operation_contract_row": invoice["name"],
                "voice_log_name": voice_log,
                "invoice_log_row": invoice_log,
                "rate": rate,
            }
        )
    return voices


@frappe.whitelist()
def edit_voice_consumption(operation_contract):
    pass
