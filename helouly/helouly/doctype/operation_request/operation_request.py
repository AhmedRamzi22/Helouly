# Copyright (c) 2023, Smart Solution and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
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
)
from erpnext.stock.get_item_details import get_item_price
from erpnext.stock.get_item_details import get_item_details


class OperationRequest(Document):
    def validate(self):
        self.validate_device()
        self.validate_totals()

    def validate_device(self):
        for device in self.devices:
            if device.is_free_item:
                device.price = 0
                device.total = 0
                device.total_including_vat = 0

    @frappe.whitelist()
    def calc_contract_duration(self):
        if not self.contract_duration and not self.contract_start_date:
            frappe.throw(
                _("<b>Contract Start Date</b> , <b>Contract Duration</b> , <b>Total Of Month / Year</b>  Requird")
            )

        if not self.total_date or self.total_date == 0:
            frappe.throw(_("<b>Total Of Month / Year</b>  Requird"))

        if self.contract_duration == "Monthly":
            extra_day = self.total_date

        if self.contract_duration == "Yearly":
            extra_day = self.total_date * 12

        self.contract_end_date = add_months(self.contract_start_date, extra_day)

    @frappe.whitelist()
    def sum_item_group_totals(self):
        self.items_details_contract = []
        item_group_map = []
        child_tables = [
            "Non-Recurring Charges Contract",
            "Monthly Subscription Contract",
            "Contract Devices",
        ]

        for table in child_tables:
            item_group = frappe.db.get_list(
                table,
                filters={"parent": self.name, "parenttype": "Operation Contract"},
                group_by="item_group",
                fields=["sum(qty) as qty", "sum(total_including_vat) as total_including_vat", "item_group"],
            )

            if len(item_group):
                for item in item_group:
                    item_group_map.append(item)
            continue

        merged_item_group = merge_and_sum_items(item_group_map)

        for item in merged_item_group:
            if item["total_including_vat"] == None:
                continue
            self.append(
                "items_details_contract",
                {
                    "item_group": item["item_group"],
                    "total_including_vat": float(item["total_including_vat"]),
                    "qty": float(item["qty"]),
                },
            )

    @frappe.whitelist()
    def get_item_details(self, item=None):
        item_group, item_name, description = frappe.db.get_value(
            "Item", item, ["item_group", "item_name", "description"]
        )
        rate = frappe.db.get_value("Item Price", {"item_code": item}, ["price_list_rate"])
        tax = frappe.db.get_list("Item Tax", filters={"parent": item, "parenttype": "Item"}, pluck="item_tax_template")

        if len(tax):
            tax = tax[0]
            vat_rate = get_item_tax_rate(tax)

            for k, v in vat_rate.items():
                vat_rate = v
            total_price = ((float(vat_rate) / 100) * rate) + rate

        else:
            tax = ""
            total_price = rate
            vat_rate = 0

        if not rate:
            rate = 0

        return {
            "rate": rate,
            "item_group": item_group,
            "item_name": item_name,
            "description": description,
            "tax": tax,
            "vat_rate": vat_rate,
            "total_price": total_price,
        }

    def validate_totals(self):
        child_tables = [
            "non_recurring_charges_contract",
            "monthly_subscription",
            "devices",
        ]
        current_doc = self.as_dict()
        for table in child_tables:
            if len(current_doc[table]):
                total = 0
                for item in current_doc[table]:
                    total += float(item.total_including_vat)
                if table == "non_recurring_charges_contract":
                    current_doc["non_recurring_charges_total"] = total
                elif table == "voices_subscription":
                    current_doc["voices_total"] = total
                elif table == "monthly_subscription":
                    current_doc["monthly_subscription_total"] = total
                elif table == "devices":
                    current_doc["devices_total"] = total

    @frappe.whitelist()
    def calc_totals(self, table):
        total = 0
        current_doc = self.as_dict()
        for item in current_doc[table]:
            total += int(item.total_including_vat)

        return total

    @frappe.whitelist()
    def recalculate_item_details(self, args):
        total = float(args["qty"]) * float(args["rate"])
        if float(args["vat_rate"]) == 0.0:
            total_vat = float(args["qty"]) * float(args["rate"])
        else:
            total_vat = (((float(args["vat_rate"]) / 100) * float(args["rate"])) + float(args["rate"])) * float(
                args["qty"]
            )

        return {
            "total": total,
            "total_price": total_vat,
        }

    @frappe.whitelist()
    def validate_free_item(self):
        total = 0
        for row in self.devices:
            if row.is_free_item == 1:
                row.price = 0
                row.total_including_vat = 0
                row.total = 0
            total += float(row.total_including_vat)
        self.devices_total = total

    @frappe.whitelist()
    def convert_lead_to_customer(self, customer_group, territory):
        lead_status = frappe.db.get_value("Lead", self.party_type, "status")
        if lead_status == "Converted":
            customer = frappe.db.exists("Customer", {"lead_name": self.party_type})
            if customer:
                frappe.db.set_value("Operation Request", self.name, "party", "Customer")
                frappe.db.set_value("Operation Request", self.name, "party_type", customer)
        else:
            customer = self.create_customer_from_lead(customer_group, territory)
            frappe.db.set_value("Operation Request", self.name, "party", "Customer")
            frappe.db.set_value("Operation Request", self.name, "party_type", customer.name)

    def create_customer_from_lead(self, customer_group, territory):
        lead = frappe.get_doc("Lead", self.party_type)
        customer = frappe.new_doc("Customer")
        customer.customer_name = lead.lead_name
        customer.customer_group = customer_group
        customer.territory = territory
        customer.mobile_no = lead.mobile_no
        customer.lead_name = self.party_type
        customer.salutation = lead.salutation
        customer.default_sales_partner = lead.sales_partner
        customer.insert()
        frappe.db.set_value("Lead", lead.name, "status", "Converted")

        return customer


def merge_and_sum_items(item_list):
    merged_items = {}

    for item in item_list:
        item_group = item["item_group"]
        qty = item["qty"]
        total = item["total_including_vat"]

        if item_group in merged_items:
            merged_items[item_group]["qty"] += qty

            if not total == None:
                merged_items[item_group]["total_including_vat"] += total
        else:
            merged_items[item_group] = {"qty": qty, "total_including_vat": total, "item_group": item_group}

    merged_item_list = list(merged_items.values())

    return merged_item_list


def get_item_tax_rate(item_tax_template):
    tax_values = frappe.db.get_value(
        "Item Tax Template Detail", {"parent": item_tax_template}, ["tax_type", "tax_rate"]
    )
    tax_dict = {tax_values[0]: tax_values[1]}
    return tax_dict


@frappe.whitelist()
def create_operation_contract(source_name, target_doc=None):
    self = frappe.get_doc("Operation Request", source_name)
    doc = frappe.new_doc("Operation Contract")
    doc.project = self.project
    doc.customer = self.party_type
    doc.sales_partner = self.sales_partner
    doc.cost_center = self.cost_center
    doc.operation_request = self.name
    doc.contract_duration = self.contract_duration
    doc.total_date = self.total_date
    doc.invoicing_periodicity = self.invoicing_periodicity
    doc.contract_start_date = self.contract_start_date
    doc.contract_end_date = self.contract_end_date
    doc.auto_renewal = self.auto_renewal
    doc.monthly_subscription = self.monthly_subscription
    doc.monthly_subscription_total = self.monthly_subscription_total
    doc.voices = self.voices
    doc.voices_subscription = self.voices_subscription
    doc.voices_total = self.voices_total
    doc.devices = self.devices
    doc.devices_total = self.devices_total
    doc.non_recurring_charges_contract = self.non_recurring_charges_contract
    doc.non_recurring_charges_total = self.non_recurring_charges_total
    doc.items_details_contract = self.items_details_contract
    doc.notes = self.notes
    return doc
