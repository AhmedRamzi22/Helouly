// Copyright (c) 2024, Smart Solution and contributors
// For license information, please see license.txt

frappe.query_reports["Department Request Status"] = {
  filters: [
    {
      fieldname: "department",
      label: __("Department"),
      fieldtype: "Link",
      options: "Department",
    },
  ],
  tree: true,

  initial_depth: 3,
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    return value;
  },
};
