// Copyright (c) 2023, Smart Solution and contributors
// For license information, please see license.txt
{% include 'helouly/public/js/utils/contract.js' %}
frappe.ui.form.on('Operation Request', {
	refresh: function(frm) {
		frm.events.party_filter(frm)
		frm.events.sum_item_group_totals(frm)
		frm.events.set_voice_filter(frm)
		frm.events.set_cost_center_filter(frm)
		frm.events.set_voice_filter_for_monthly_sub(frm)
		frm.events.set_voice_filter_for_device(frm)
		frm.events.non_recurring_charges_contract_filter(frm)
		frm.events.set_contract_btn(frm)
	  },
	  set_contract_btn:function(frm){
		if(frm.doc.docstatus !=1){
			return
		}
			frm.add_custom_button(__("Operation Contract"),async () => {
				if (frm.doc.party=="Lead"){
					let lead_name= await frappe.db.get_value('Lead', frm.doc.party_type, 'lead_name')
						.then(r => {
							return r.message.lead_name 
						})
				frappe.confirm(`Are you sure you want to convert <b> ${lead_name}</b> Lead To Customer?`,
				async() => {
								await frappe.prompt([
										{
											label: 'Customer Group',
											fieldname: 'customer_group',
											fieldtype: 'Link',
											options:"Customer Group",
											reqd: 1
										},
										{
											label: 'Territory',
											fieldname: 'territory',
											fieldtype: 'Link',
											options:"Territory",
											reqd: 1
										},
									],async (values) => {
										await frm.call({
											method: "convert_lead_to_customer",
											doc: frm.doc,
											args:{
												customer_group:values.customer_group,
												territory:values.territory,
												
											},
										
											callback: function (r) {
												
											}});
											
									frappe.model.open_mapped_doc({
										method: "helouly.helouly.doctype.operation_request.operation_request.create_operation_contract",
										frm: cur_frm
									})
								})
				}, () => {}
				
				)}else{
							frappe.model.open_mapped_doc({
								method: "helouly.helouly.doctype.operation_request.operation_request.create_operation_contract",
								frm: cur_frm
						})}},__('Create'));
		
	  },
	  project:async function(frm){
		await  frappe.db.get_value('Project',frm.doc.project, 'customer')
		  .then(r => {
			  if(!r.message.customer){
				frappe.throw(__("Please set customer in <b>Project</b>"))
	  
			  } // Open
		  })
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
	  party_filter:function(frm){
		frm.set_query("party", function () {
			return {
			  filters: {
				"name":["in",["Lead","Customer"] ],
			  
			  }
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
