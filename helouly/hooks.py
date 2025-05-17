
app_name = "helouly"
app_title = "Helouly"
app_publisher = "Smart Solution"
app_description = "telecommunication"
app_email = "info@smartsoleg.com"
app_license = "smart"
required_apps = ["erpnext"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/helouly/css/helouly.css"
#app_include_js = "/assets/helouly/js/helouly.js"
#app_include_js = "/assets/erpnext/js/lead.js"





# include js, css files in header of web template
# web_include_css = "/assets/helouly/css/helouly.css"
# web_include_js = "/assets/helouly/js/helouly.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "helouly/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}

doctype_list_js = {"Lead": "public/js/lead.js",
                   "Opportunity": "public/js/opportunity.js"}

# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# In your_app/hooks.py


# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "helouly.utils.jinja_methods",
# 	"filters": "helouly.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "helouly.install.before_install"
# after_install = "helouly.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "helouly.uninstall.before_uninstall"
# after_uninstall = "helouly.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "helouly.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Department Request Form": "helouly.events.department_request_form.requester_permission",
}
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    # "*": {
    # 	"on_update": "method",
    # 	"on_cancel": "method",
    # 	"on_trash": "method"
    # }
    "Sales Invoice": {
        "before_submit": "helouly.controller.sales_invoice.change_contract_invoice_status",
        "on_trash": "helouly.controller.sales_invoice.on_trash",
        "before_cancel": "helouly.controller.sales_invoice.on_trash",
        "validate": "helouly.controller.sales_invoice.validate_contract",
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    # 	"all": [
    # 		"helouly.tasks.all"
    # 	],
    # "daily": [],
    "hourly": ["helouly.tasks.generate_sales_invoice.generate_sales_invoice"],
    # 	"weekly": [
    # 		"helouly.tasks.weekly"
    # 	],
    # 	"monthly": [
    # 		"helouly.tasks.monthly"
    # 	],
}

# Testing
# -------

# before_tests = "helouly.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "helouly.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "helouly.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["helouly.utils.before_request"]
# after_request = ["helouly.utils.after_request"]

# Job Events
# ----------
# before_job = ["helouly.utils.before_job"]
# after_job = ["helouly.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"helouly.auth.validate"
# ]
