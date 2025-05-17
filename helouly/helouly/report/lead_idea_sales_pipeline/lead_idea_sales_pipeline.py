import frappe
from frappe import _

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
            "options": "Lead",
            "width": 170,
            "background": "#ebeef0",
        },


{
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 80,
            "background": "#ebeef0",
        },



        {
            "fieldname": "team_leader",
            "label": _("Team Leader"),
            "fieldtype": "Data",
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
            "fieldname": "company_name",
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
            "fieldname": "industry",
            "label": _("Sector"),
            "fieldtype": "Link",
            "options": "Industry Type",
            "width": 120,
        },
        {
            "fieldname": "city",
            "label": _("City"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "mobile_no",
            "label": _("Mobile No"),
            "fieldtype": "Data",
            "width": 150,
            "color": "darkblue",
        },
    ]
    return columns

def get_data(filters):
    data = []
    conditions = ""

    if filters.get("status"):
        conditions += " AND status = '{0}'".format(filters.get("status"))
    
    if filters.get("team_leader"):
        conditions += " AND team_leader = '{0}'".format(filters.get("team_leader"))

    if filters.get("sales_partner"):
        conditions += " AND sales_partner = '{0}'".format(filters.get("sales_partner"))

   
    if filters.get("industry"):
        conditions += " AND industry = '{0}'".format(filters.get("industry"))

    
    try:
        sql_query = """SELECT * FROM `tabLead` WHERE 1=1 {0}""".format(conditions)
        fetched_data = frappe.db.sql(sql_query, as_dict=True)

        for record in fetched_data:
            data.append({
                "name": record.get("name"),
                "status": record.get("status"),
                "team_leader": record.get("team_leader"),
                "sales_partner": record.get("sales_partner"),
                "company_name": record.get("company_name"),
                "lead_name": record.get("lead_name"),
                "industry": record.get("industry"),
                "city": record.get("city"),
                "mobile_no": record.get("mobile_no"),
                            })
    except Exception as e:
        frappe.log_error("Error in fetching data: {0}".format(str(e)))

    return data
