import frappe
from frappe.utils import (
    add_days,
    add_months,
    cint,
    date_diff,
    flt,
    get_datetime,
    get_last_day,
    getdate,
    month_diff,
    nowdate,
    today,
    now,
)
import json
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


def generate_sales_invoice():
    invoice_log = frappe.get_list(
        "Invoice Log",
        filters={"invoice_date": ["<=", today()], "status": "Pending"},
        fields=["operation_contract", "invoice_date", "name"],
    )

    for invoice in invoice_log:
        create_sales_invoice(invoice)


def create_sales_invoice(invoice):
    if not frappe.db.exists(
        "Operation Contract", {"name": invoice["operation_contract"]}
    ):
        return
    docstatus = frappe.db.get_value(
        '"Operation Contract"', invoice["operation_contract"], "docstatus"
    )

    if docstatus == 2:
        return

    operation_contract = frappe.get_doc(
        "Operation Contract", invoice["operation_contract"]
    )
    invoice_log = frappe.get_doc("Invoice Log", invoice["name"])

    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.project = operation_contract.project
    sales_invoice.cost_center = operation_contract.cost_center
    sales_invoice.operation_contract = operation_contract.name
    sales_invoice.invoice_log = invoice_log.name
    sales_invoice.set_posting_time = 1
    sales_invoice.customer = operation_contract.customer
    sales_invoice.due_date = invoice["invoice_date"]
    sales_invoice.posting_date = invoice["invoice_date"]
    sales_invoice.terms = operation_contract.notes
    for item in invoice_log.items:
        if item.is_free_item == 1:
            sales_invoice.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": 0,
                    "price_list_rate": 0.00,
                    "is_free_item": item.is_free_item,
                    "project": operation_contract.project,
                },
            )
        elif item.voice == 1:
            sales_invoice.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "is_free_item": item.is_free_item,
                    "voice_row": item.row_name,
                    "project": operation_contract.project,
                },
            )
        else:
            sales_invoice.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "is_free_item": item.is_free_item,
                    "project": operation_contract.project,
                },
            )

    sales_invoice.insert()
    if not sales_invoice.taxes_and_charges:
        for item in sales_invoice.items:
            add_taxes_from_tax_template(item, sales_invoice)
            calculate_taxes_and_totals(sales_invoice)
        sales_invoice.save()
    frappe.db.set_value("Invoice Log", invoice_log.name, "status", "Invoiced")

    for inv in operation_contract.invoices_payment:
        if inv.invoice_due_date == invoice["invoice_date"]:
            inv.status = "Created"
            frappe.db.set_value(
                "Invoices Contract",
                inv.name,
                "sales_invoice_series",
                sales_invoice.name,
            )
            inv.creation1 = now()


def add_taxes_from_tax_template(child_item, parent_doc, db_insert=True):
    add_taxes_from_item_tax_template = frappe.db.get_single_value(
        "Accounts Settings", "add_taxes_from_item_tax_template"
    )

    if child_item.get("item_tax_rate") and add_taxes_from_item_tax_template:
        tax_map = json.loads(child_item.get("item_tax_rate"))
        for tax_type in tax_map:
            tax_rate = flt(tax_map[tax_type])

            taxes = parent_doc.get("taxes") or []
            # add new row for tax head only if missing
            found = any(tax.account_head == tax_type for tax in taxes)
            if not found:
                tax_row = parent_doc.append("taxes", {})
                tax_row.update(
                    {
                        "description": str(tax_type).split(" - ")[0],
                        "charge_type": "On Net Total",
                        "account_head": tax_type,
                        "rate": 0,
                    }
                )
