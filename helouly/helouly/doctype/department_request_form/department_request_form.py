import frappe
from frappe.model.document import Document
from frappe.utils.data import getdate, now_datetime, add_to_date, nowtime,today
from datetime import datetime, timedelta, time
from dateutil.parser import parse  
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
from frappe.exceptions import OutgoingEmailError
class DepartmentRequestForm(Document):

    def before_submit(self):
        self.assign_head() 
        # self.calculate_time_info()
       
    def before_insert(self):
         self.created_by= frappe.session.user
    def validate(self):
      
        self.validate_attachments()
        self.fetch_head_of_department_user()

        if self.workflow_state == "Waiting HoD Approval":
            self.send_user_notification()

        if self.workflow_state == "Approved":
            self.request_status = "Under Processing"


    def on_update_after_submit(self):
        self.calculate_resolved_time()

    def assign_head(self):
        from frappe.desk.form import assign_to
        user = frappe.get_value("Employee", self.employee, "user_id")
        if not user:
            return
        assign_to.add(
            {
                "assign_to": [user],
                "doctype": self.doctype,
                "name": self.name,
                "description": "Close this task",
            }
        )

    
    def calculate_time_info(self):
        self.created_on = datetime.now()
        resolve_time = frappe.get_value(
            "Department Request Type", self.request_type, "time"
        )
        if resolve_time:
            resolve_time = float(resolve_time)
            # Splitting the float into hours and minutes
            hours = int(resolve_time)
            minutes = int((resolve_time - hours) * 60)
            
            created_on_datetime = datetime.now()
            # Adding hours and minutes to the creation time
            self.deadline = created_on_datetime + timedelta(hours=hours, minutes=minutes)
            self.deadline = self.deadline.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] 

            if not self.shift_type:
                return
            
            end_hours =  self.shift_end.total_seconds() // 3600
            end_minutes = ( self.shift_end.total_seconds() % 3600) // 60
            end_seconds =  self.shift_end.total_seconds() % 60

            if datetime.strptime(self.deadline, '%Y-%m-%d %H:%M:%S.%f') <=  datetime.combine(datetime.now().date(), datetime.min.time()) + timedelta(hours=end_hours, minutes=end_minutes, seconds=end_seconds):
               return 
            

            shift_start = self.shift_start
            shift_end = self.shift_end

            holiday_list = frappe.get_value("Shift Type", self.shift_type, "holiday_list")
            
            holiday_dates = frappe.get_all(
                "Holiday",
                filters={

                    "parent": holiday_list
                },
                pluck="holiday_date"
            )
            weekdays =  [getdate(holiday).weekday() for holiday in holiday_dates]
            current_date = self.created_on
            shift_duration = shift_end - shift_start
            twenty_four_hours = timedelta(hours=24)
            adjusted_shift_duration = shift_duration - twenty_four_hours
            adjusted_shift_duration = abs(adjusted_shift_duration.total_seconds() / 3600)


            redate = self.deadline
            redate = datetime.strptime(self.deadline, '%Y-%m-%d %H:%M:%S.%f')
            # current_date = datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S.%f')
            
            while current_date <= redate:

                if current_date.weekday() in weekdays:
                    redate += timedelta(days=1)
                    current_date += timedelta(days=1)
                    continue

                else:
                    shift_datetime = datetime.strptime(str(shift_end),'%H:%M:%S')
                    deadline_datetime = datetime.strptime(self.deadline, '%Y-%m-%d %H:%M:%S.%f')

                    if getdate(self.deadline) == getdate(today() ) and  deadline_datetime.strftime('%H:%M:%S') < shift_datetime.strftime('%H:%M:%S'):

                        current_date += timedelta(days=1)

                        continue
                       
                    else:
                        redate += timedelta(hours=int(adjusted_shift_duration))

                        current_date += timedelta(days=1)
            self.deadline = redate



    def calculate_resolved_time(self):
        if self.request_status in ["Resolved", "Closed"]:
            self.resolved_on = now_datetime()
 
    @frappe.whitelist()
    def set_attachments_names(self):

        request_type = frappe.get_all("Required Attachment",filters={"parenttype":"Department Request Type", "parent":self.request_type},pluck='attachment_name')

        self.required_attachments = []

        if len(request_type):
            for att in request_type:

                self.append("required_attachments",
                            {
                                "attachment_name": att
                            })
                
    def validate_attachments(self):
        
        if  len(self.required_attachments):
            for att in self.get("required_attachments"):
                if not att.get("attach"):
                    frappe.throw(_("You should set all required attachments"))
    def fetch_head_of_department_user(self):

        if not self.assign_to:
            if self.employee:
                hd_user=frappe.db.get_value("Employee",self.employee,"user_id")
                if not hd_user:
                    frappe.throw("Please set user  to Head Of Department Employee")
                self.assign_to=hd_user

    def send_user_notification(self):
        user=frappe.session.user
        employee=frappe.db.get_value("Employee",{"user_id":user},"employee_name")
       
        if not employee:
            frappe.throw("Current user not assigned to employee")

        department=frappe.db.get_value("Employee",{"employee_name":employee},"department")
        subject="<b style='font-size:14px; font-weight: 900;'> Request by :</b> {0} - ({1})  <br> <b style=' font-weight: 900'>Request Type</b>: {2}  <br> <b style=' font-weight: 900'>Department</b>: {3}".format(employee,department,self.request_type,self.department)
        users=self.get_users(employee)
        
        if len(users):
            for user in users:
                send_notify(self,user,subject)
            
            try:
                frappe.sendmail(recipients=users,subject="You have been assigned to a new request",message=subject,reference_doctype="Department Request Form",reference_name=self.name)
            
            except OutgoingEmailError:
                frappe.log_error("Outgoing email account not configured", "Email Sending Error")
                frappe.msgprint("Could not send the email because the outgoing email account is not configured. Please contact your administrator.")
            
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Unknown Email Sending Error")
                frappe.msgprint(f"An error occurred while sending the email: {str(e)}")
    
    
    def get_users(self,employee):
        users=[self.assign_to]
        owner_managers=get_employee_managers(employee)
        head_department_manager=get_employee_managers(self.employee)
        setting_manager=get_setting_manager()
        notify_users=users+owner_managers+head_department_manager+setting_manager
        return notify_users
    
    @frappe.whitelist() 
    def send_poke(self,message):
        if message:
            manager_user=frappe.db.get_value("Employee",{"name":self.employee} , "user_id")
           
            if self.assign_to == manager_user:
                    send_notify(self,self.assign_to,message)
                    try:
                        frappe.sendmail(recipients=[self.assign_to],subject="<b>{0}</b> Poke You ".format(frappe.session.user),message=message,reference_doctype="Department Request Form",reference_name=self.name)
                    except OutgoingEmailError:
                            frappe.log_error("Outgoing email account not configured", "Email Sending Error")
                            frappe.msgprint("Could not send the email because the outgoing email account is not configured. Please contact your administrator.")
                    except Exception as e:
                            frappe.log_error(frappe.get_traceback(), "Unknown Email Sending Error")
                            frappe.msgprint(f"An error occurred while sending the email: {str(e)}")
            else:
                    
                    send_notify(self,self.assign_to,message)
                    send_notify(self,manager_user,message)
                    try:
                        frappe.sendmail(cc=[manager_user],recipients=[self.assign_to],subject="<b>{0}</b> Poke You ",message=message,reference_doctype="Department Request Form",reference_name=self.name)
                    except OutgoingEmailError:
                            frappe.log_error("Outgoing email account not configured", "Email Sending Error")
                            frappe.msgprint("Could not send the email because the outgoing email account is not configured. Please contact your administrator.")
                    except Exception as e:
                            frappe.log_error(frappe.get_traceback(), "Unknown Email Sending Error")
                            frappe.msgprint(f"An error occurred while sending the email: {str(e)}")

    @frappe.whitelist()      
    def set_assignee(self,employee):
        self.flags.ignore_permissions = True
        user=frappe.db.get_value("Employee",{"name":employee} , "user_id")
        if not user:
            frappe.throw("Please assign user to employee :<b>{0}</b>".format(employee))
            
        frappe.db.set_value("Department Request Form",self.name ,"assign_to",user)
        

        frappe.db.set_value("Department Request Form",self.name ,"employee_name",employee)
        assigner=frappe.db.get_value("Employee",{"user_id":frappe.session.user},"employee_name")
        if not assigner:
            assigner= frappe.session.user
        subject="<b style='font-size:14px; font-weight: 900;color:green; '> You have been assigned to a new request &#128584; &#128584;:</b>  <br> <b style=' font-weight: 900'>Request Type</b>: {0}  <br> <b style=' font-weight: 900'>Department</b>: {1} <br> <b style=' font-weight: 900'>assigner</b>: {2}  ".format(self.request_type,self.department,assigner)
        send_notify(self,user,subject)
        try:
            frappe.sendmail(recipients=[user],subject="You have been assigned to a new request",message=subject,reference_doctype="Department Request Form",reference_name=self.name)
        except OutgoingEmailError:
                frappe.log_error("Outgoing email account not configured", "Email Sending Error")
                frappe.msgprint("Could not send the email because the outgoing email account is not configured. Please contact your administrator.")
        except Exception as e:
                frappe.log_error(frappe.get_traceback(), "Unknown Email Sending Error")
                frappe.msgprint(f"An error occurred while sending the email: {str(e)}")
@frappe.whitelist()
def count_closed_request():
    user = frappe.session.user
    filter={ "request_status": "Closed",
            }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["assign_to"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
@frappe.whitelist()
def count_open_request():
    user = frappe.session.user
    filter={ "request_status": "Open",
          }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["assign_to"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                
                users.extend(employee_users)
           
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}


@frappe.whitelist()
def count_under_processing_request():
    user = frappe.session.user
    
    filter={ "request_status": "Under Processing",
           }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["assign_to"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
   
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
@frappe.whitelist()
def count_resolved_request():
    user = frappe.session.user
    filter={ "request_status": "Resolved",
          }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["assign_to"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
@frappe.whitelist()
def count_overdue_request():
    user = frappe.session.user
    filter={ "request_status": "Overdue",
           }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["assign_to"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}

@frappe.whitelist()
def count_my_closed_request():
    user = frappe.session.user
    filter={ "request_status": "Closed",
            }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["created_by"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
@frappe.whitelist()
def count_my_open_request():
    user = frappe.session.user
    filter={ "request_status": "Open",
           }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["created_by"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}


@frappe.whitelist()
def count_my_under_processing_request():
    user = frappe.session.user
    
    filter={ "request_status": "Under Processing",
            }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["created_by"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
@frappe.whitelist()
def count_my_resolved_request():
    user = frappe.session.user
    filter={ "request_status": "Resolved",
          }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["created_by"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
@frappe.whitelist()
def count_my_overdue_request():
    user = frappe.session.user
    filter={ "request_status": "Overdue",
         }
    if user != "Administrator":
        if "Request (Employee)" in frappe.permissions.get_roles(user) and "Request HOD" not in frappe.permissions.get_roles(user):
            filter["created_by"]=frappe.session.user
        
        if "Request HOD" in frappe.permissions.get_roles(user):
            hod = frappe.db.get_value("Employee", {"user_id": user}, "name")
            users = [user]

            if hod:
                # Use the recursive function to get all subordinates
                employee_users = get_all_subordinates(hod)
                users.extend(employee_users)
            
            filter["assign_to"] = ["in", users]

    number = frappe.db.count("Department Request Form", filter)
    return{
	"value": number,
	"fieldtype": "Int",
	"route_options": filter,
	"route": ["List", "Department Request Form"]
}
def get_all_subordinates(hod):
    # Recursively get all subordinates under the HOD
    subordinates = frappe.db.get_all("Employee", filters={"reports_to": hod}, pluck="user_id")
    all_subordinates = list(subordinates)
    
    for subordinate in subordinates:
        emp_name = frappe.db.get_value("Employee", {"user_id": subordinate}, "name")
        if emp_name:
            deeper_subordinates = get_all_subordinates(emp_name)
            all_subordinates.extend(deeper_subordinates)
    
    return all_subordinates
def get_employee_managers(employee_id):
    managers = []
    current_employee_id = employee_id

    while current_employee_id:
        manager_id = frappe.db.get_value("Employee",{"employee_name":current_employee_id} , "reports_to")
       
        if manager_id:
            user=frappe.db.get_value("Employee",manager_id , "user_id")
            
            if user:
                managers.append(user)
            current_employee_id = manager_id 
        else:
            break  
    
    return managers

def get_setting_manager():
    managers=[]
    setting=frappe.get_doc('Department Request Setting')
    if len(setting.user):
        for  i in setting.user:
            managers.append(i.user)
    return managers

def send_notify(self,user,subject):
    
    
        notification_doc = {
            "type": "Assignment",
            "document_type": "Department Request Form",
            "subject":subject,
            "document_name": self.name,
            "from_user": frappe.session.user,
            "email_content": None,
        }
        enqueue_create_notification(user,notification_doc),