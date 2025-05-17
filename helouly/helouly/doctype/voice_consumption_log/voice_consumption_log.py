# Copyright (c) 2023, Smart Solution and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VoiceConsumptionLog(Document):
    def validate(self):
        operation_contract = frappe.get_doc("Operation Contract", self.operation_contract)
        self.add_item_to_invoice_log()
        self.mark_invoices_payment(operation_contract)
        self.mark_voices_subscription(operation_contract)
        operation_contract.save()

    def mark_voices_subscription(self, operation_contract):
        for item in operation_contract.voices_subscription:
            if item.name == self.voices_subscription_row_name:
                item.invoiced = 1

    def mark_invoices_payment(self, operation_contract):
        for item in operation_contract.invoices_payment:
            if item.name == self.invoices_schedual_row_name:
                item.voiced = 1
                item.invoice_amount = float(self.invoice_current_amount) + float(self.consumption_amount)

    def add_item_to_invoice_log(self):
        invoice_log = frappe.get_doc("Invoice Log", self.invoice_log)
        invoice_log.append(
            "items",
            {
                "item_code": self.voice,
                "rate": float(self.consumption_amount),
                "qty": 1,
                "row_name": self.name,
                "voice": 1,
            },
        )
        invoice_log.save()
