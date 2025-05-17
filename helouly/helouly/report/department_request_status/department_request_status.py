
import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return Requests(filters).run()

class Requests:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})

    def run(self):
        self.get_columns()
        self.get_data()
        self.get_chart_data()
        skip_total_row = 0
        return self.columns, self.data, None,self.chart  , None, skip_total_row

    def get_columns(self):
        
        self.columns = [
             {
            "label": _("Department"),
            "fieldname": "department",
            "fieldtype": "Data",
          
            "width": 200,
        }, {
            "label": _("Employee Name"),
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 200,
        },
          {
            "label": _("Open"),
            "fieldname": "open",
            "fieldtype": "Data",
       
            "width": 120,
        },
          {
            "label": _("Under Processing"),
            "fieldname": "under_processing",
            "fieldtype": "Data",
            "width": 150,
        },
          {
            "label": _("Overdue"),
            "fieldname": "overdue",
            "fieldtype": "Data",
       
            "width": 120,
        },
          {
            "label": _("Resolved"),
            "fieldname": "resolved",
            "fieldtype": "Data",
       
            "width": 120,
        },
          {
            "label": _("Closed"),
            "fieldname": "closed",
            "fieldtype": "Data",
       
            "width": 120,
        }
        ]

    def get_data(self):
        
        self.data = []
        filter = None
        self.department=[]

        if "department" in self.filters:
            filter={"name":self.filters["department"]}
        departments = frappe.db.get_all("Department", filters=filter, pluck="name")

        if len(departments):
            for department in departments:

                if department == "All Departments":
                    continue

                department_data = {}
                department_data["department"] = department
                department_data["indent"] = 0
                
                employees_data = []
                employees = frappe.db.get_all("Employee", filters={"department": department,"status":"Active"}, fields=["*"])
                
                if len(employees):
                    total_dict={
                          "department":"<b style='font-size:10px; color:cornflowerblue;'>Total Department ({0})  </b>".format(department),
                        "open":0,
                    "under_processing":0,
                    "overdue":0,
                    "resolved":0,
                    "closed":0}
        
                    status_dict={
                        
                        "Open":"open",
                        "Under Processing":"under_processing",
                        "Overdue":"overdue",
                        "Resolved":"resolved",
                        "Closed":"closed"
                    }
                    employees_data = []

                    for employee in employees:
                        employee_data = {}
                        e_data=frappe.db.get_all("Department Request Form",filters={"employee_name":employee["name"]},  fields=['request_status', "count(name) as count"], group_by='request_status')
                        
                        if len(e_data):

                            for status in e_data:
                                employee_data["employee_name"] = employee["employee_name"]
                                employee_data[status_dict[status["request_status"]]]=status["count"]
                                total_dict[status_dict[status["request_status"]]]+=status["count"]
                                employee_data["indent"] = 1
                            employees_data.append(employee_data)

                    self.data.append(department_data)  
                    self.data.extend(employees_data)
                    self.data.append(total_dict)
                    self.department.append({department:total_dict["under_processing"]})
                    
    def get_chart_data(self):
        self.chart  = {}
        departments=[]
        under_processing_count = []

        for i in self.department:
            
            for k,v in i.items():
                departments.append(k)
                under_processing_count.append(v)
                
        if not len(departments):
             return  self.chart
        
        labels = departments
        self.chart  = {
            "data": {"labels": labels, "datasets": [{"name":"Under Processing", "values": under_processing_count}]},
            "type": "bar",
        }

       
