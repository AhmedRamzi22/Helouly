import frappe



def requester_permission(user):
    user = frappe.session.user

    if user == "Administrator":
        return "1=1"  
    if "Request (Employee)" not in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
        return "1=1" 

    if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
        return """(`tabDepartment Request Form`.created_by = {user} OR `tabDepartment Request Form`.assign_to = {user})""".format(
            user=frappe.db.escape(user)
        )
    
    if "Request HOD" in frappe.permissions.get_roles(user):
        hod = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
        employee_users = []

        if hod:
            employee_users = get_all_subordinates(hod)
            
        users = [frappe.session.user] + employee_users
      
        return """(`tabDepartment Request Form`.created_by IN ({users}) OR `tabDepartment Request Form`.assign_to IN ({users}))""".format(
            users=", ".join(frappe.db.escape(user) for user in users)
        )

def get_all_subordinates(hod):
    
    subordinates = frappe.db.get_all("Employee", filters={"reports_to": hod}, pluck="user_id")
    all_subordinates = list(subordinates)
    
    for subordinate in subordinates:
        emp_name = frappe.db.get_value("Employee", {"user_id": subordinate}, "name")
        if emp_name:
            deeper_subordinates = get_all_subordinates(emp_name)
            all_subordinates.extend(deeper_subordinates)
    
    return all_subordinates
