frappe.ui.form.on("Monthly Subscription Contract", {
  item:(frm, cdt, cdn)=>{
    let row = locals[cdt][cdn];
    frm.events.tables_controller(frm,row,"monthly_subscription","monthly_subscription_total")
  },
  qty:(frm, cdt, cdn)=>{
    let row = locals[cdt][cdn];
    frm.events.recalculate_tables(frm,row,"monthly_subscription","monthly_subscription_total")
  },
  price:(frm, cdt, cdn)=>{
    let row = locals[cdt][cdn];
    frm.events.recalculate_tables(frm,row,"monthly_subscription","monthly_subscription_total")
  }
  })


  frappe.ui.form.on("Voices Subscription Contract", {
    item:(frm, cdt, cdn)=>{
      let row = locals[cdt][cdn];
      frm.events.tables_controller(frm,row,"voices_subscription","voices_total")
    },
    qty:(frm, cdt, cdn)=>{
      let row = locals[cdt][cdn];
      frm.events.recalculate_tables(frm,row,"voices_subscription","voices_total")
    },
    price:(frm, cdt, cdn)=>{
      let row = locals[cdt][cdn];
      frm.events.recalculate_tables(frm,row,"voices_subscription","voices_total")
    }})


  frappe.ui.form.on("Contract Devices", {
      item:(frm, cdt, cdn)=>{
        let row = locals[cdt][cdn];
        frm.events.tables_controller(frm,row,"devices","devices_total")
      },
      qty:(frm, cdt, cdn)=>{
        let row = locals[cdt][cdn];
        frm.events.recalculate_tables(frm,row,"devices","devices_total")
      },
      price:(frm, cdt, cdn)=>{
        let row = locals[cdt][cdn];
        frm.events.recalculate_tables(frm,row,"devices","devices_total")
      },
      is_free_item:async (frm, cdt, cdn)=>{
        let row = locals[cdt][cdn];
        frm.events.recalculate_tables(frm,row,"devices","devices_total")
       await frm.call({
          method: "validate_free_item",
          doc: frm.doc,
          callback: function (r) {}});
        cur_frm.refresh_field("devices")
}})

  
frappe.ui.form.on("Non-Recurring Charges Contract", {
  item:(frm, cdt, cdn)=>{
    let row = locals[cdt][cdn];
    frm.events.tables_controller(frm,row,"non_recurring_charges_contract","non_recurring_charges_total")
  },
  qty:(frm, cdt, cdn)=>{
    let row = locals[cdt][cdn];
    frm.events.recalculate_tables(frm,row,"non_recurring_charges_contract","non_recurring_charges_total")
  },
  price:(frm, cdt, cdn)=>{
    let row = locals[cdt][cdn];
    frm.events.recalculate_tables(frm,row,"non_recurring_charges_contract","non_recurring_charges_total")
  }})
  