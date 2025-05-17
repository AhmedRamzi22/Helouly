import frappe
from frappe.utils import now
from frappe import _


def change_contract_invoice_status(self, event):
    if self.operation_contract and self.invoice_log:
        operation_contract = frappe.get_doc("Operation Contract", self.operation_contract)
        for item in operation_contract.invoices_payment:
            if item.invoice_log == self.invoice_log:
                item.status = "Submitted"
                item.amount_after_submitted = self.grand_total
        operation_contract.save()


def on_trash(self, event):
    if self.operation_contract and self.invoice_log:
        try:
            operation_contract = frappe.get_doc("Operation Contract", self.operation_contract)
        except frappe.DoesNotExistError:
            return
        if operation_contract.docstatus != 2:
            for invoice in operation_contract.invoices_payment:
                if invoice.invoice_log == self.invoice_log:
                    invoice.status = "Not Created"
                    invoice.creation1 = ""
                    invoice.sales_invoice_series = ""
            operation_contract.save()
            frappe.db.set_value("Invoice Log", self.invoice_log, "status", "Pending")


def validate_contract(self, event):
    if self.operation_contract and self.invoice_log:
        try:
            operation_contract = frappe.get_doc("Operation Contract", self.operation_contract)
        except frappe.DoesNotExistError:
            frappe.throw(_("Contract is deleted"))

        if operation_contract.docstatus == 2:
            frappe.throw(_("Contract is cancelled"))
        invoice_log = frappe.get_doc("Invoice Log", self.invoice_log)

        frappe.db.set_value("Invoice Log", self.invoice_log, "status", "Invoiced")

        for inv in operation_contract.invoices_payment:
            if inv.invoice_due_date == invoice_log.invoice_date:
                inv.status = "Created"
                frappe.db.set_value("Invoices Contract", inv.name, "sales_invoice_series", self.name)
                inv.creation1 = now()
        operation_contract.save()
