// Copyright (c) 2025, Henderson Villegas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Provisiones', {
	onload: function(frm) {

		frappe.db.get_value('Property Setter', {'doc_type': 'Journal Entry', 'property':'options', 'field_name':'naming_series'}, 'value', (value) => {
			frm.set_df_property('naming_series', "options", value.value.split('\n'));

			if(!frm.is_new()){
				frm.set_value('naming_series', frm.doc.naming_series);
			}

			frm.refresh_fields()
		});

		if(frm.is_new()){
			frm.doc.asientos_contables_generados = [];
			frm.doc.estado = 'Nuevo'
			frm.refresh_fields()
		}

	},
	refresh: (frm, cdt, cdn) => {
		if(!frm.is_new()){

			if(frm.doc.asientos_contables_generados.length > 0 && (frm.doc.estado == '' || frm.doc.estado == undefined)){
				frm.doc.estado = 'Ejecutado';
				frm.refresh_fields()
			}

			frm.add_custom_button('Crear Asiento', () => {
				
				if(frm.doc.estado != 'En Proceso'){
					frappe.prompt([
						{'fieldname': 'start_date', 'fieldtype': 'Date', 'label': 'Fecha Inicio', 'reqd': 1},
						{'fieldname': '', 'fieldtype': 'Column Break', 'label': ''},
						{'fieldname': 'end_date', 'fieldtype': 'Date', 'label': 'Fecha Fin', 'reqd': 1}
					],
					function(values){
	
						frm.doc.estado = 'En Proceso'
						frm.refresh_fields()

						if(new Date(values.start_date) > new Date(values.end_date)) {
							frappe.msgprint("Fecha Fin debe ser mayor a Fecha Inicio"); return;
						}
	
						frm.doc['start_date'] = values.start_date
						frm.doc['end_date'] = values.end_date
						
						frappe.call({
							doc: frm.doc,
							method: "create_journal_entry",
							callback: function(r) {

								frm.doc.estado = 'Ejecutado'
								frm.refresh_fields()

								if(!r.exc) {
									if(r.message) {
										if(r.message.success){
											frappe.msgprint({
												title: __('Notification'),
												indicator: 'green',
												message: `Se ha creado el asiento contable ${r.message.journal}`
											});
										}else{
											frappe.msgprint({
												title: __('Notification'),
												indicator: 'red',
												message: `No se ha crea asiento contable`
											});
										}
									}
								}
								frm.reload_doc();
							}
						});
	
						
					},
					'Rango de Fechas',
					'Generar Asiento Contable'
					);
				}else
				{
					frappe.msgprint({
						title: __('Notification'),
						indicator: 'red',
						message: `Existe una creacion en proceso`
					});
				}
				

			})
		}
	}
});
