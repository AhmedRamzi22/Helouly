// Copyright (c) 2023, Smart Solution and contributors
// For license information, please see license.txt
{% include 'helouly/public/js/utils/contract.js' %}
frappe.ui.form.on("Operation Contract", {

  refresh: function(frm) {
    frm.events.sum_item_group_totals(frm)
    frm.events.call_consumption_btn_add(frm)
    frm.events.call_consumption_btn_deduction(frm)
    frm.events.set_voice_filter(frm)
    frm.events.set_cost_center_filter(frm)
    frm.events.set_voice_filter_for_monthly_sub(frm)
    frm.events.set_voice_filter_for_device(frm)
    frm.events.non_recurring_charges_contract_filter(frm)

  },
  project:async function(frm){
  await  frappe.db.get_value('Project',frm.doc.project, 'customer')
    .then(r => {
        if(!r.message.customer){
          frappe.throw(__("Please set customer in <b>Project</b>"))

        } 
    })
  },
  call_consumption_btn_deduction:function(frm){
    if(frm.doc.docstatus!=1){
      return
    }
    frm.add_custom_button('Edit', () => {
      let d = new frappe.ui.Dialog({
        title: __("Edit Call Consumption"),
        size: "large",
        fields: [
          {
            fieldtype: "Link",
            fieldname: "voice",
            label: __("Voice"),
            options:"Item",
            default:frm.doc.voices[0].item,
            read_only: 1,
           
           
        
          },
          {
            fieldname: "voices",
            fieldtype: "Table",
            label: "Voices",
            fields: [
            
              {
                fieldtype: "Date",
                fieldname: "due_date",
                label: __("Posting Date"),
                read_only: 1,
                in_list_view: 1,
            
              },
            {
                fieldtype: "Float",
                fieldname: "current_price",
                label: __("Current Price"),
                in_list_view: 1,
                read_only: 1,
              },
              {
                fieldtype: "Float",
                fieldname: "new_price",
                label: __("New Price"),
                in_list_view: 1,
               
              },
              {
                fieldtype: "Data",
                fieldname: "operation_contract_row",
                label: __("operation_row"),
                in_list_view: 1,
                hidden: 1,
              },
              {
                fieldtype: "Data",
                fieldname: "voice_log_name",
                label: __("voice_log_name"),
                in_list_view: 1,
                hidden: 1,
              },
              {
                fieldtype: "Data",
                fieldname: "invoice_log_row",
                label: __("invoice_log_row"),
                in_list_view: 1,
                hidden: 1,
              },
            
        
            
            ],
          },
      
        ],
        primary_action_label: __("Confirm"),
             async    primary_action(values) {  
     let selected_items =
                    d.fields_dict.voices.grid.get_selected_children();
                  if (selected_items.length == 0) {
                    frappe.throw({
                      message: "Please select <b>Voices</b> from the Table",
                      title: __("Call Consumption"),
                      indicator: "blue",
                    });
                  }
              await    frm.call({
                    method: "edit_call_consumption",
                    doc: frm.doc,
                    args:values,
                  
                    callback: function (r) {
                    
                    },
                  });
                 
                  d.hide();
                  window.location.reload();
                
}})
                let po_items = [];
              async  function set_voices(d) {

                    let current_data= await frappe.call({
                          method: "helouly.utils.get_voice_consumption",
                          args: {
                            operation_contract:frm.docname
                          },
                          callback: function (r) {
                            return r.message

                          }})
                          for (let row in current_data.message){
                                      
                                      po_items.push({
                                    
                                        due_date: current_data.message[row].date,
                                        current_price:current_data.message[row].rate,
                                        operation_contract_row:current_data.message[row].operation_contract_row,
                                        voice_log_name:current_data.message[row].voice_log_name,
                                        invoice_log_row:current_data.message[row].invoice_log_row,
                                        

                                      });
                                    
                                    }
                                  
                     d.fields_dict["voices"].df.data = po_items;
                     d.get_field("voices").refresh();
                    }
                     set_voices(d);
                     d.get_field("voices").grid.only_sortable();
                     d.get_field("voices").refresh();
             
              d.show()
              }, 'Call Consumption')
              },
               
                  
               
              
           


  
  call_consumption_btn_add:function(frm){
    if(frm.doc.docstatus!=1){
      return
    }
    
  frm.add_custom_button('Add', () => {
    let d = new frappe.ui.Dialog({
      title: __("Add Call Consumption"),
      size: "large",
      fields: [
        {
          fieldtype: "Link",
          fieldname: "voice",
          label: __("Voice"),
          options:"Item",
          default:frm.doc.voices[0].item,
          read_only: 1,
         
         
      
        },
        {
          fieldname: "voices",
          fieldtype: "Table",
          label: "Voices",
          fields: [
          
            {
              fieldtype: "Date",
              fieldname: "due_date",
              label: __("Posting Date"),
              read_only: 1,
              in_list_view: 1,
          
            },
          {
              fieldtype: "Float",
              fieldname: "price",
              label: __("Price"),
              in_list_view: 1,
            },
      
          
          ],
        },
    
      ],
      primary_action_label: __("Confirm"),
              async primary_action(values) {
                 
                  let selected_items =
                  d.fields_dict.voices.grid.get_selected_children();
                if (selected_items.length == 0) {
                  frappe.throw({
                    message: "Please select <b>Voices</b> from the Table",
                    title: __("Call Consumption"),
                    indicator: "blue",
                  });
                }
                
                for(let i in selected_items ){
                  if ( selected_items[i]["due_date"]){
                  let row=cur_frm.add_child('voices_subscription', {
                        item: values.voice,
                        price: selected_items[i]["price"]?? 0,
                        posting_date:selected_items[i]["due_date"]
                    });
              
                }}
               
                 await cur_frm.save("Update");
                 
                await frm.call({
                  method: "set_call_consumption",
                  doc: frm.doc,
                
                  callback: function (r) {
                  
                  },
                });
                window.location.reload();
                  d.hide();
              }})
              let po_items = [];
              function set_voice(d) {
                  cur_frm.doc.invoices_payment.forEach((d) => {
                      if (!d.voiced && d.status !="Submitted"){
                      po_items.push({
                    
                          due_date: d.invoice_due_date
                      });
                    }
                  });
                d.fields_dict["voices"].df.data = po_items;
              
                  d.get_field("voices").refresh();
                }
                set_voice(d);
                d.get_field("voices").grid.only_sortable();
                d.get_field("voices").refresh();
                // d.wrapper.find(".grid-heading-row .grid-row-check").click();
                if(po_items.length==0){
                  frappe.msgprint("All invoices have received call consumption")
                }else{ d.show();}
                
      }, 'Call Consumption');
  },
  set_cost_center_filter:function(frm){
    frm.set_query("cost_center", function () {
      return {
        filters: [
          ["is_group", "=", 0],
        
        ],
      };
    });
 
  },
  set_voice_filter:function(frm){
    frm.fields_dict['voices'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
      var d = locals[cdt][cdn];
      return {
          filters: [
              [ 'voice', '=',1]
          ]
      };
  };
  },
  set_voice_filter_for_monthly_sub:function(frm){
    frm.fields_dict['monthly_subscription'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
      var d = locals[cdt][cdn];
      return {
          filters: [
              [ 'voice', '=',0]
          ]
      };
  };
  },
  set_voice_filter_for_device:function(frm){

    frm.fields_dict['devices'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
      var d = locals[cdt][cdn];
      return {
          filters: [
              [ 'voice', '=',0]
          ]
      };
  };
  },
  non_recurring_charges_contract_filter:function(frm){

    frm.fields_dict['non_recurring_charges_contract'].grid.get_field('item').get_query = function(doc, cdt, cdn) {
      var d = locals[cdt][cdn];
      return {
          filters: [
              [ 'voice', '=',0]
          ]
      };
  };
  },

  sum_item_group_totals:function(frm){
  frm.call({
    method: "sum_item_group_totals",
    doc: frm.doc,
  
    callback: function (r) {
 
    },
  });},
  contract_start_date: function (frm) {
    frm.events.calc_contract_duration(frm);
  },
  contract_duration: function (frm) {
    frm.events.calc_contract_duration(frm);
  },
  total_date: function (frm) {
    frm.events.calc_contract_duration(frm);
  },
  calc_contract_duration: function (frm) {
    if (!frm.doc.total_date || !frm.doc.contract_start_date || !frm.doc.contract_duration ) {
      return
    }
    
    frm.call({
      method: "calc_contract_duration",
      doc: frm.doc,
      freeze: true,
      callback: function () {
        cur_frm.refresh_field("contract_end_date")
      },
    });
 
  },
  tables_controller:async function(frm,row,table,total_field){
    if (row.item){
      let price= await frm.call({
        method: "get_item_details",
        doc: frm.doc,
        args:{
          "item":row.item
        },
        
        callback: function (r) {
          return r
        },
      });
      
      row.price=parseInt( price.message["rate"])
      row.qty=1
      row.total=parseInt( price.message["rate"])
      row.vat=price.message["tax"]
      row.vat_rate=price.message["vat_rate"]
      row.total_including_vat= parseInt( price.message["total_price"])
      await frm.call({
        method: "calc_totals",
        doc: frm.doc,
        args:{
          "table":table,
      },
        callback: function (r) {
          frm.set_value(total_field,parseFloat( r.message))
        },
      });
      cur_frm.refresh_field(table)
      }
  },
  recalculate_tables:async function(frm,row,table,total_field){
    let price= await frm.call({
      method: "recalculate_item_details",
      doc: frm.doc,
      args:{
        "qty":row.qty,
        "rate":row.price,
        "vat_rate":row.vat_rate
  
    },
      
      callback: function (r) {
        return r
      },
    });
    row.total=price.message["total"]
    row.total_including_vat= parseInt( price.message["total_price"])
    await frm.call({
      method: "calc_totals",
      doc: frm.doc,
      args:{
        "table":table,
    },
      callback: function (r) {
        frm.set_value(total_field,parseFloat( r.message))
      },
    });
    cur_frm.refresh_field(table)
  }
});

