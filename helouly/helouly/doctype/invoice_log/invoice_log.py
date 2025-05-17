# Copyright (c) 2023, Smart Solution and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InvoiceLog(Document):
    def validate(self):
        self.calc_total()

    def calc_total(self):
        total_amount = 0
        for item in self.items:
            if item.total_including_vat:
                total_amount += float(item.total_including_vat)
            else:
                total_amount += float(item.rate)

        self.total = total_amount
