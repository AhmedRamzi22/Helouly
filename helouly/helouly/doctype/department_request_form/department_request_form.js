// Copyright (c) 2024, Smart Solution and contributors
// For license information, please see license.txt

frappe.ui.form.on("Department Request Form", {
  onload(frm) {
    frm.get_field("required_attachments").grid.only_sortable();
    setInterval(function () {
      frm.set_intro("");
      frm.trigger("set_form_intro");
    }, 60000);
  },
  after_save(frm) {
    setInterval(function () {
      frm.set_intro("");
      frm.trigger("set_form_intro");
    }, 60000);
  },
  refresh(frm) {
    frm.events.assign_btn(frm);
    frm.events.change_assign_btn(frm);
    frm.events.poke_btn(frm);
    frm.set_query("request_type", function () {
      return {
        filters: [["department", "=", frm.doc.department]],
      };
    });

    frm.trigger(" ");
    frm.trigger("set_form_intro");
  },
  poke_btn: function (frm) {
    if (!frm.is_new()) {
      frm.add_custom_button("Poke", () => {
        var d = new frappe.ui.Dialog({
          title: __("Poke"),
          fields: [
            {
              label: "Message",
              fieldname: "message",
              fieldtype: "Text",
            },
          ],
          primary_action: function (value) {
            frm.call({
              method: "send_poke",
              doc: frm.doc,
              args: { message: value.message },
              callback: async function (r) {
                await frm.reload_doc();
                d.hide();
              },
            });
          },
        });
        d.show();
      });
    }
  },
  assign_btn: function (frm) {
    if (frm.doc.docstatus == 1 && frm.doc.employee_name == frm.doc.employee) {
      frm
        .add_custom_button("Assign", () => {
          var d = new frappe.ui.Dialog({
            title: __("Assign"),
            fields: [
              {
                label: "Employee",
                fieldname: "employee",
                fieldtype: "Link",
                options: "Employee",
                get_query: function () {
                  return {
                    filters: {
                      department: frm.doc.department,
                    },
                  };
                },
              },
            ],
            primary_action: function (value) {
              frm.call({
                method: "set_assignee",
                doc: frm.doc,
                args: { employee: value.employee },
                callback: async function (r) {
                  await frm.reload_doc();
                  d.hide();
                },
              });
            },
          });
          d.show();
        })
        .addClass("btn-primary");
    }
  },
  change_assign_btn: function (frm) {
    if (frm.doc.docstatus == 1 && frm.doc.employee_name != frm.doc.employee) {
      frm
        .add_custom_button("Change Assign", () => {
          var d = new frappe.ui.Dialog({
            title: __("Assign"),
            fields: [
              {
                label: "Employee",
                fieldname: "employee",
                fieldtype: "Link",
                options: "Employee",
                get_query: function () {
                  return {
                    filters: {
                      department: frm.doc.department,
                      user_id: ["!=", frm.doc.assign_to],
                    },
                  };
                },
              },
            ],
            primary_action: function (value) {
              frm.call({
                method: "set_assignee",
                doc: frm.doc,
                args: { employee: value.employee },
                callback: async function (r) {
                  await frm.reload_doc();
                  d.hide();
                },
              });
            },
          });
          d.show();
        })
        .addClass("btn-primary");
    }
  },
  set_form_intro: function (frm) {
    var intro_data = get_intro_data(frm.doc);
    var intro_text = get_intro_text(intro_data, frm.doc);
    var intro_color = get_intro_color(frm.doc, intro_data);

    frm.set_intro(`<b>${intro_text}</b>`, intro_color);
  },

  department: function (frm) {
    frm.set_query("request_type", function () {
      return {
        filters: [["department", "=", frm.doc.department]],
      };
    });
  },

  request_type: function (frm) {
    frappe.call({
      doc: frm.doc,
      method: "set_attachments_names",

      callback: function (r) {
        frm.refresh_fields("required_attachments");
      },
    });

    frm.refresh_fields("required_attachments");
  },
});
function get_intro_data(doc) {
  var remaining = Math.max(
    moment(doc.deadline).diff(moment(), "milliseconds"),
    moment().diff(moment(doc.deadline), "milliseconds")
  );

  var duration = moment.duration(remaining);
  var remaining_days = duration.days();
  var remaining_hours = duration.hours();
  var remaining_minutes = duration.minutes();

  var resolved_on_date = moment(doc.resolved_on);
  var creation_date = moment(doc.created_on);
  var resolve_duration = moment.duration(resolved_on_date.diff(creation_date));

  var resolve_days = resolve_duration.days();
  var resolve_hours = resolve_duration.hours();
  var resolve_minutes = resolve_duration.minutes();

  return {
    remaining_days,
    remaining_hours,
    remaining_minutes,
    resolve_days,
    resolve_hours,
    resolve_minutes,
    now_datetime: frappe.datetime.now_datetime(),
    duration,
  };
}

function get_intro_text(intro_data, doc) {
  const intial_remaining_text = `${intro_data.remaining_days}d - ${intro_data.remaining_hours}h - ${intro_data.remaining_minutes}m`;
  const intial_resolved_text = `Resolved in ${intro_data.resolve_days}d - ${intro_data.resolve_hours}h - ${intro_data.resolve_minutes}m`;

  if (
    doc.deadline > intro_data.now_datetime &&
    doc.request_status !== "Resolved"
  ) {
    return `${intial_remaining_text} Remaining`;
  }

  if (
    doc.request_status !== "Resolved" &&
    doc.deadline < intro_data.now_datetime
  ) {
    console.log(intro_data.duration);
    return `${intial_remaining_text} Elapsed`;
  }

  if (doc.request_status === "Resolved" && doc.deadline > doc.resolved_on) {
    return intial_resolved_text;
  }

  if (doc.request_status === "Resolved" && doc.deadline <= doc.resolved_on) {
    return `${intial_resolved_text} Lately`;
  }

  return "";
}

function get_intro_color(doc, intro_data) {
  if (
    doc.request_status !== "Resolved" &&
    doc.deadline > intro_data.now_datetime
  ) {
    return intro_data.remaining_days === 0 ? "yellow" : "blue";
  }

  if (
    doc.request_status !== "Resolved" &&
    doc.deadline < intro_data.now_datetime
  ) {
    return "red";
  }

  if (doc.request_status === "Resolved" && doc.deadline > doc.resolved_on) {
    return "green";
  }

  if (doc.request_status === "Resolved" && doc.deadline <= doc.resolved_on) {
    return "red";
  }

  return "";
}
