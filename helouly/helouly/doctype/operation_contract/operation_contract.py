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
import calendar
import copy
from erpnext.stock.get_item_details import get_item_price
from erpnext.stock.get_item_details import get_item_details
import json
from frappe.utils import add_to_date, get_datetime, getdate
from datetime import datetime, timedelta, date

from frappe.utils.data import (
    get_first_day,
    get_first_day_of_week,
    get_last_day,
    get_last_day_of_week,
    get_quarter_ending,
    get_quarter_start,
    get_year_ending,
    get_year_start,
)


class OperationContract(Document):
    def before_submit(self):
        self.generate_invoice()

    def before_cancel(self):
        self.check_submitted_invoice()

    def on_update_after_submit(self):
        self.validate_voice_total()
        self.validate_totals()

    def before_validate(self):
        self.validate_free_item()
        self.sum_item_group_totals()
        self.validate_device()
        self.validate_totals()
        self.validate_voice()

    def check_submitted_invoice(self):
        for invoice in self.invoices_payment:
            if invoice.invoice_log:
                voice_log = frappe.db.get_value("Voice Consumption Log", {"invoice_log": invoice.invoice_log}, ["name"])

                if voice_log:
                    self.delete_documnet("Voice Consumption Log", voice_log)
                self.delete_documnet("Invoice Log", invoice.invoice_log)

            if invoice.status == "Submitted":
                frappe.throw(_("Please cancelled Submitted invoices"))

            if invoice.status == "Created" and invoice.sales_invoice_series:
                self.delete_documnet("Sales Invoice", invoice.sales_invoice_series)
        self.invoices_payment = []

    def delete_documnet(self, doctype, doc):
        doc = frappe.get_doc(doctype, doc)
        doc.delete()
        frappe.db.commit()

    def validate_device(self):
        for device in self.devices:
            if device.is_free_item:
                device.price = 0
                device.total = 0
                device.total_including_vat = 0

    def validate_voice(self):
        if len(self.voices) > 1:
            frappe.throw(_("Please set one voice"))

    @frappe.whitelist()
    def set_call_consumption(self):
        for item in self.voices_subscription:
            if item.invoiced == 0:
                invoice = self.get_the_right_invoice(item.posting_date)
                voice = self.create_voice_consumption_log(invoice, item)
                if invoice["status"] == "Created":
                    sales_invoice = frappe.get_doc("Sales Invoice", invoice["sales_invoice_series"])
                    sales_invoice.append(
                        "items", {"item_code": item.item, "qty": 1, "rate": item.price, "voice_row": voice.name}
                    )
                    sales_invoice.save()

    def create_voice_consumption_log(self, invoice, item):
        voice_consumption_doc = frappe.new_doc("Voice Consumption Log")
        voice_consumption_doc.operation_contract = self.name
        voice_consumption_doc.invoice_date = item.posting_date
        voice_consumption_doc.voice = item.item
        voice_consumption_doc.invoice_log = invoice["invoice_log"]
        voice_consumption_doc.voices_subscription_row_name = item.name
        voice_consumption_doc.invoices_schedual_row_name = invoice["name"]
        voice_consumption_doc.invoice_current_amount = invoice["invoice_amount"]
        voice_consumption_doc.consumption_amount = item.price
        voice_consumption_doc.insert()
        return voice_consumption_doc

    def add_item_to_invoice_log(self, invoice, item):
        invoice_log = frappe.get_doc("Invoice Log", invoice["invoice_log"])
        invoice_log.append(
            "items",
            {
                "item_code": item.item,
                "rate": item.price,
                "qty": 1,
                "row_name": item.name,
                "voice": 1,
            },
        )
        invoice_log.save()

    def get_the_right_invoice(self, posting_date):
        posting_date = add_days(posting_date, 1)
        invoice = frappe.db.get_all(
            "Invoices Contract",
            filters={"parent": self.name, "invoice_due_date": ["<", posting_date]},
            fields=["invoice_log", "idx", "invoice_amount", "name", "status", "sales_invoice_series"],
            order_by="invoice_due_date desc",
        )

        if len(invoice):
            invoice = invoice[0]
        else:
            frappe.throw(_("No valid invoice for <b>{0}</b>".format(posting_date)))
        return invoice

    def generate_invoice(self):
        total_invoice_days = date_diff(self.contract_end_date, self.contract_start_date)
        first_date, installment, dates, posting_date = self.get_dates()
        date_len = len(dates) + 1
        first_invoice_log = self.get_first_invoice_fees(total_invoice_days, date_len)

        invoice_dates = dates[:-1]
        date_trace = first_date

        for date in invoice_dates:
            helouly_setting = frappe.get_doc("Helouly Settings")
            next_invoice_date = get_first_day_of_next_month_with_day(str(date_trace), 1)
            total_charge_days = date_diff(next_invoice_date, date_trace)

            last_invoice_log = self.get_rest_of_invoices(total_charge_days, total_invoice_days, date, date_len)
            date_trace = next_invoice_date
        last_invoice = dates[-2]
        last_date = dates[-1]
        last_days = date_diff(self.contract_end_date, last_invoice) + 1

        last_invoice_log = self.get_invoice_fees_for_last(last_days, total_invoice_days, last_date)

    def get_rest_of_invoices(self, account_day, total_invoice_days, date, date_len):
        helouly_setting = frappe.get_doc("Helouly Settings")

        total_charge_days = account_day

        first_fees, first_items = self.get_invoice_item_fees_for_rest(total_charge_days, total_invoice_days, date_len)

        invoice_log = self.create_invoice_log(first_items, date, total_charge_days, date)

        self.append(
            "invoices_payment",
            {
                "invoice_due_date": date,
                "invoice_amount": first_fees,
                "invoice_log": invoice_log,
                "status": "Not Created",
            },
        )

    def get_invoice_fees_for_last(self, account_day, total_invoice_days, date):
        helouly_setting = frappe.get_doc("Helouly Settings")

        total_charge_days = account_day

        first_fees, first_items = self.get_invoice_item_fees_for_last(total_charge_days, total_invoice_days)

        invoice_log = self.create_invoice_log(first_items, date, total_charge_days, date)

        self.append(
            "invoices_payment",
            {
                "invoice_due_date": date,
                "invoice_amount": first_fees,
                "invoice_log": invoice_log,
                "status": "Not Created",
            },
        )

    def get_invoice_fees(self, account_day, total_invoice_days, date):
        helouly_setting = frappe.get_doc("Helouly Settings")

        total_charge_days = account_day

        first_fees, first_items = self.get_invoice_item_fees(total_charge_days, total_invoice_days)

        invoice_log = self.create_invoice_log(first_items, date, total_charge_days, date)

        self.append(
            "invoices_payment",
            {
                "invoice_due_date": date,
                "invoice_amount": first_fees,
                "invoice_log": invoice_log,
                "status": "Not Created",
            },
        )

    def get_first_invoice_fees(self, total_invoice_days, date_len):
        first_invoice = frappe.db.get_all(
            "Invoices Contract", filters={"parent": self.name, "first_invoice": 1}, pluck="invoice_log"
        )

        if not len(first_invoice):
            first_invoice_log = self.create_invoice_log_with_first(total_invoice_days, date_len)

        else:
            first_invoice_log = first_invoice[0]

        return first_invoice_log

    def create_invoice_log_with_first(self, total_invoice_days, date_len):
        non_recurring_fees, non_recurring_items = 0, []  # Initialize these variables as empty lists

        if self.get_non_recurring_charges_fees():
            non_recurring_fees, non_recurring_items = self.get_non_recurring_charges_fees()

        first_date, installment, dates, posting_date = self.get_dates()

        accounting_days = date_diff(str(first_date), self.contract_start_date) - 1

        first_fees, first_items = self.get_invoice_item_fees(accounting_days, total_invoice_days, first_date, date_len)

        item = first_items + non_recurring_items
        fees = non_recurring_fees + float(first_fees)
        validate_total = 0.0
        for i in item:
            validate_total += float(i.total_including_vat)
        if validate_total == 0:
            return
        invoice_log = self.create_invoice_log(item, first_date, accounting_days, posting_date)

        self.append(
            "invoices_payment",
            {
                "invoice_due_date": posting_date,
                "invoice_amount": fees,
                "invoice_log": invoice_log,
                "status": "Not Created",
                "first_invoice": 1,
            },
        )
        return first_date

    def create_invoice_log(self, valid_items, first_date, accounting_days, posting_date):
        invoice_log = frappe.new_doc("Invoice Log")
        invoice_log.operation_contract = self.name
        invoice_log.invoice_date = posting_date
        invoice_log.project = self.project

        invoice_log.customer = self.customer
        invoice_log.first_invoice = 1
        total = 0
        for item in valid_items:
            if hasattr(item, "is_free_item"):
                is_free_item = item.is_free_item
            else:
                is_free_item = 0
            total += float(item.total_including_vat)
            invoice_log.append(
                "items",
                {
                    "item_code": item.item,
                    "item_name": item.item_name,
                    "item_group": item.item_group,
                    "description": item.description,
                    "rate": item.total_including_vat,
                    "qty": item.qty,
                    "is_free_item": is_free_item,
                    "item_tax_template": item.vat,
                    "total_including_vat": item.total_including_vat,
                    "row_name": item.name,
                },
            )
        invoice_log.total = total

        invoice_log.insert()
        return invoice_log.name

    def get_invoice_item_fees_for_rest(self, accounting_days, total_invoice_days, date_len):
        total_fees = 0
        subscription_items = []

        for sub in self.monthly_subscription:
            new_sub = copy.copy(sub)
            new_sub.qty = 1
            item = new_sub

            total_fees += item.total_including_vat
            subscription_items.append(item)

        for device in self.devices:
            new_device = copy.copy(device)
            if new_device.is_free_item:
                device.price = 0
                device.total = 0
                device.total_including_vat = 0
                subscription_items.append(new_device)
            else:
                item = self.change_item_price_months(new_device, accounting_days, total_invoice_days, date_len)
                total_fees += item.total_including_vat
                subscription_items.append(item)

        return total_fees, subscription_items

    def get_invoice_item_fees_for_last(self, accounting_days, total_invoice_days):
        total_fees = 0
        subscription_items = []
        first_date, installment, dates, posting_date = self.get_dates()
        date_len = len(dates) + 1
        first_days = date_diff(str(first_date), self.contract_start_date) - 1

        for sub in self.monthly_subscription:
            new_sub = copy.copy(sub)
            new_sub.qty = 1
            item = new_sub

            total_fees += item.total_including_vat
            subscription_items.append(item)

        for device in self.devices:
            new_device = copy.copy(device)
            if new_device.is_free_item:
                device.price = 0
                device.total = 0
                device.total_including_vat = 0
                subscription_items.append(new_device)
            else:
                item = self.change_item_price_months(new_device, accounting_days, total_invoice_days, date_len)
                total_fees += item.total_including_vat
                subscription_items.append(item)

        return total_fees, subscription_items

    def get_invoice_item_fees(self, accounting_days, total_invoice_days, first_date, date_len):
        total_fees = 0
        subscription_items = []

        for sub in self.monthly_subscription:
            new_sub = copy.copy(sub)
            new_sub.qty = 1

            last_day_of_month = get_last_day(self.contract_start_date)

            input_date = datetime.strptime(self.contract_start_date, "%Y-%m-%d").date()
            accounting_days = last_day_of_month.day - input_date.day

            num_days = calendar.monthrange(input_date.year, input_date.month)[1]

            new_sub.price = (new_sub.price / num_days) * accounting_days
            new_sub.total_including_vat = (new_sub.total_including_vat / 30) * accounting_days

            total_fees += new_sub.total_including_vat
            subscription_items.append(new_sub)

        for device in self.devices:
            new_device = copy.copy(device)
            if new_device.is_free_item:
                device.price = 0
                device.total = 0
                device.total_including_vat = 0
                subscription_items.append(new_device)
            else:
                item = self.change_item_price_months(new_device, accounting_days, total_invoice_days, date_len)

                total_fees += item.total_including_vat
                subscription_items.append(item)

        return total_fees, subscription_items

    def change_item_price_months(self, item, accounting_days, total_invoice_days, date_len):
        item.price = item.price / date_len

        item.total = item.price * item.qty
        item.total_including_vat = (((float(item.vat_rate) / 100) * float(item.price)) + float(item.price)) * float(
            item.qty
        )
        return item

    def change_item_price_based_on_days(self, item, accounting_days, total_invoice_days):
        item.price = ((item.price / total_invoice_days)) * accounting_days

        item.total = item.price * item.qty
        item.total_including_vat = (((float(item.vat_rate) / 100) * float(item.price)) + float(item.price)) * float(
            item.qty
        )
        return item

    def get_dates(self):
        dates = get_dates_from_timegrain(self.contract_start_date, self.contract_end_date, self.invoicing_periodicity)

        helouly_setting = frappe.get_doc("Helouly Settings")
        invoice_date = add_days(dates[0], 1)

        first_date = invoice_date

        correct_date = []
        installment = len(dates)
        dates = dates[1:]

        for date in dates:
            correct_date.append(add_days(date, 1))

        return first_date, installment, correct_date, invoice_date

    def get_non_recurring_charges_fees(self):
        if not len(self.non_recurring_charges_contract):
            return
        fees = 0
        non_recurring_item = []
        for item in self.non_recurring_charges_contract:
            fees += float(item.total_including_vat)
            if float(item.total_including_vat) > 0:
                non_recurring_item.append(item)
        return fees, non_recurring_item

    def check_if_first_invoice(self):
        for invoice in self.invoices_payment:
            if invoice.first_invoice and invoice.status == "Not Created":
                return True
        return False

    def get_invoice_log(self):
        pass

    def get_available_total(self):
        total = 0
        child_tables = [
            "Non-Recurring Charges Contract",
            "Monthly Subscription Contract",
            "Contract Devices",
        ]
        filters = {"parent": self.name, "parenttype": "Operation Contract"}
        for table in child_tables:
            if table == "Contract Devices":
                filters["is_free_item"] = 0
            price = frappe.db.get_all(
                table,
                filters=filters,
                fields=["sum(total_including_vat) as total"],
            )

            if price[0]["total"] != None:
                total += price[0]["total"]
        return total

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
            item_group = frappe.db.get_all(
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
    def get_item_details(self, item=None):
        item_group, item_name, description = frappe.db.get_value(
            "Item", item, ["item_group", "item_name", "description"]
        )
        rate = frappe.db.get_value("Item Price", {"item_code": item}, ["price_list_rate"])
        tax = frappe.db.get_all("Item Tax", filters={"parent": item, "parenttype": "Item"}, pluck="item_tax_template")

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

    @frappe.whitelist()
    def calc_totals(self, table):
        total = 0
        current_doc = self.as_dict()
        for item in current_doc[table]:
            total += int(item.total_including_vat)

        return total

    @frappe.whitelist()
    def validate_voice_total(self):
        total_voices = 0
        for item in self.voices_subscription:
            total_voices += item.price
        frappe.db.set_value(self.doctype, self.name, "voices_total", total_voices)

        self.reload()

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
    def edit_call_consumption(self, args):
        if len(args.get("voices")):
            for voice in args.get("voices"):
                for invoice in self.invoices_payment:
                    invoice_amount = invoice.invoice_amount - voice["current_price"]
                    invoice_amount = invoice_amount + voice["new_price"]
                    if invoice.invoice_due_date == voice["due_date"]:
                        frappe.db.set_value("Invoices Contract", invoice.name, "invoice_amount", invoice_amount)
                for item in self.voices_subscription:
                    if item.posting_date == voice["due_date"]:
                        frappe.db.set_value("Voices Subscription Contract", item.name, "price", voice["new_price"])

                frappe.db.set_value("Invoice Log Items", voice["invoice_log_row"], "rate", voice["new_price"])
                frappe.db.set_value(
                    "Voice Consumption Log", voice["voice_log_name"], "consumption_amount", voice["new_price"]
                )
                sales_item = frappe.db.get_all(
                    "Sales Invoice Item",
                    filters={"voice_row": voice["voice_log_name"]},
                    pluck="parent",
                )

                if len(sales_item):
                    sales_invoice = frappe.get_doc("Sales Invoice", sales_item[0])
                    for item in sales_invoice.items:
                        if item.voice_row == voice["voice_log_name"]:
                            item.rate = voice["new_price"]
                    sales_invoice.save()


def get_item_tax_rate(item_tax_template):
    tax_values = frappe.db.get_value(
        "Item Tax Template Detail", {"parent": item_tax_template}, ["tax_type", "tax_rate"]
    )
    tax_dict = {tax_values[0]: tax_values[1]}
    return tax_dict


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


def get_dates_from_timegrain(from_date, to_date, timegrain="Daily"):
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    days = months = years = 0

    if "Monthly" == timegrain:
        months = 1
    elif "Quarterly" == timegrain:
        months = 3
    elif "Annually" == timegrain:
        months = 12
    elif "Half-Yearly" == timegrain:
        # Half Annually is treated as two semi-annual periods (6 months each)
        months = 6
        dates = [get_period_ending(from_date, timegrain)]
        while getdate(dates[-1]) < getdate(to_date):
            date = get_period_ending(add_to_date(dates[-1], years=years, months=months, days=days), timegrain)
            dates.append(date)
        return dates

    dates = [get_period_ending(from_date, timegrain)]

    while getdate(dates[-1]) < getdate(to_date):
        date = get_period_ending(add_to_date(dates[-1], years=years, months=months, days=days), timegrain)
        dates.append(date)

    return dates


def get_period_ending(date, timegrain):
    return getdate(
        {
            "Monthly": get_last_day(date),
            "Quarterly": get_quarter_ending(date),
            "Annually": get_year_ending(date),
            "Half-Yearly": get_half_year_ending(date),
        }[timegrain]
    )


def get_first_days(date):
    first = get_first_day(date)
    date = add_to_date(first, months=1)
    return date


def get_half_year_ending(date):
    # Calculate the ending date for a half-yearly period
    if date.month <= 6:
        return date.replace(month=6, day=30)  # End of June for the first half
    else:
        return date.replace(month=12, day=31)


def get_first_day_of_next_month_with_day(input_date_str, day):
    # Convert the input date string to a datetime.date object
    input_date = datetime.strptime(input_date_str, "%Y-%m-%d").date()

    # Calculate the year and month of the next month
    if input_date.month == 12:
        next_year = input_date.year + 1
        next_month = 1
    else:
        next_year = input_date.year
        next_month = input_date.month + 1

    # Create a date object for the first day of the next month
    first_day_of_next_month = date(next_year, next_month, 1)

    # Calculate the target day of the next month
    target_day_of_next_month = first_day_of_next_month.replace(day=day)

    # If the target day is before the input date, add a month to it
    if target_day_of_next_month < input_date:
        if target_day_of_next_month.month == 12:
            next_year = target_day_of_next_month.year + 1
            next_month = 1
        else:
            next_year = target_day_of_next_month.year
            next_month = target_day_of_next_month.month + 1
        target_day_of_next_month = target_day_of_next_month.replace(year=next_year, month=next_month)

    return target_day_of_next_month


def get_day_in_same_or_previous_month(input_date_str, day):
    # Convert the input date string to a datetime.date object
    input_date = datetime.strptime(input_date_str, "%Y-%m-%d").date()

    # Calculate the year and month of the current month based on the input date
    current_year = input_date.year
    current_month = input_date.month

    # Calculate the target day in the current month
    target_day_in_current_month = date(current_year, current_month, day)

    # Check if the target day is valid in the current month
    if target_day_in_current_month < input_date:
        return target_day_in_current_month
    else:
        # Calculate the year and month of the previous month
        if current_month == 1:
            previous_year = current_year - 1
            previous_month = 12
        else:
            previous_year = current_year
            previous_month = current_month - 1

        # Calculate the target day in the previous month
        target_day_in_previous_month = date(previous_year, previous_month, day)

        return target_day_in_previous_month
