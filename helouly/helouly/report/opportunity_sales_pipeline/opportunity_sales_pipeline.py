import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns =  [

       {
            "fieldname": "name",
            "label": _("ID"),
            "fieldtype": "Link",
            "options": "Opportunity",
            "width": 150,
         },

        {
            "fieldname": "transaction_date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 120,
        },


        {
            "fieldname": "team_leader",
            "label": _("Team Leader"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 120,
        },
        
{
            "fieldname": "sales_partner",
            "label": _("Sales Partner"),
            "fieldtype": "Link",
            "options": "Sales Partner",
            "width": 120,
        },
{
            "fieldname": "operators",
            "label": _("Operator"),
            "fieldtype": "Link",
            "options": "Operators",
            "width": 100,
        },
{
            "fieldname": "opportunity_product_type",
            "label": _("Product Type"),
            "fieldtype": "Link",
            "options": "Opportunity Product Type",
            "width": 150,
        },
        {
            "fieldname": "opportunity_product",
            "label": _("Product"),
            "fieldtype": "Link",
            "options": "Opportunity Product",
            "width": 120,
        },
        
        {
            "fieldname": "organization_name",
            "label": _("Organization Name"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "lead_name",
            "label": _("Lead Name"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "sales_stage",
            "label": _("Sales Stage"),
            "fieldtype": "Link",
            "options": "Sales Stage",
            "width": 120,
        },
        {
            "fieldname": "opportunity_amount",
            "label": _("Opportunity Amount"),
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "industry",
            "label": _("Sector"),
            "fieldtype": "Link",
            "options": "Industry Type",
            "width": 120,
        },
        {
            "fieldname": "probability",
            "label": _("Probability"),
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "fieldname": "city",
            "label": _("City"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "expected_closing_date",
            "label": _("Expected Closing Date"),
            "fieldtype": "Date",
            "width": 150,
        },

       {
            "fieldname": "opportunity_age",
            "label": _("Ageing"),
            "fieldtype": "Int",
            "width": 80,
         },

    ]


    return columns

def get_data(filters):
    data = []
    conditions = ""

    if filters.get("from_date"):
        from_date = datetime.strptime(filters.get("from_date"), "%Y-%m-%d").strftime('%Y-%m-%d %H:%M:%S')
        conditions += " AND transaction_date >= '{0}'".format(from_date)

    if filters.get("to_date"):
        to_date = datetime.strptime(filters.get("to_date"), "%Y-%m-%d").strftime('%Y-%m-%d %H:%M:%S')
        conditions += " AND transaction_date <= '{0}'".format(to_date)

    if filters.get("team_leader"):
        conditions += " AND team_leader = '{0}'".format(filters.get("team_leader"))

    if filters.get("sales_partner"):
        conditions += " AND sales_partner = '{0}'".format(filters.get("sales_partner"))

    if filters.get("opportunity_product_type"):
        conditions += " AND opportunity_product_type = '{0}'".format(filters.get("opportunity_product_type"))

    if filters.get("opportunity_product"):
        conditions += " AND opportunity_product = '{0}'".format(filters.get("opportunity_product"))

    if filters.get("sales_stage"):
        conditions += " AND sales_stage = '{0}'".format(filters.get("sales_stage"))

    if filters.get("industry"):
        conditions += " AND industry = '{0}'".format(filters.get("industry"))

    try:
        sql_query = """SELECT * FROM `tabOpportunity` WHERE 1=1 {0}""".format(conditions)
        fetched_data = frappe.db.sql(sql_query, as_dict=True)

        for record in fetched_data:
            data.append({
                "name": record.get("name"),
                "transaction_date": record.get("transaction_date"),
                "team_leader": record.get("team_leader"),
                "sales_partner": record.get("sales_partner"),
                "operators": record.get("operators"),
                "opportunity_product_type": record.get("opportunity_product_type"),
                "opportunity_product": record.get("opportunity_product"),
                "organization_name": record.get("organization_name"),
                "lead_name": record.get("lead_name"),
                "sales_stage": record.get("sales_stage"),
                "opportunity_amount": record.get("opportunity_amount"),
                "industry": record.get("industry"),
                "probability": record.get("probability"),
                "city": record.get("city"),
                "expected_closing_date": record.get("expected_closing"),
                "opportunity_age": record.get("opportunity_age")
            })
    except Exception as e:
        frappe.log_error("Error in fetching data: {0}".format(str(e)))

    return data
