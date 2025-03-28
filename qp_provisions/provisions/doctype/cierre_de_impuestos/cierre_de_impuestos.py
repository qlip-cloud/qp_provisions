# Copyright (c) 2025, Henderson Villegas and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
from frappe import _

class CierredeImpuestos(Document):
	@frappe.whitelist()
	def create_closing_taxes(self):

		all_accounts = []

		for c in self.cerrar_cuentas:
			if frappe.db.exists("Account", c.account):
				lft, rgt = frappe.db.get_value("Account", c.account, ["lft", "rgt"])
				children = frappe.get_all("Account", filters={"lft": [">=", lft], "rgt": ["<=", rgt]})
				all_accounts += [c.name for c in children]
			else:
				frappe.throw(_("Account: {0} does not exist").format(c))

		if len(all_accounts) > 1:
			all_accounts = f' in {tuple(all_accounts)}'
		else:
			all_accounts = f" = '{all_accounts[0]}'"
		
		dr = frappe.db.sql(f"""
				SELECT 	party, 
					party_type, 
					account, 
					(SUM(credit) - SUM(debit)) as saldo 
				FROM `tabGL Entry`	
				WHERE posting_date >= '{self.start_date}'
				AND posting_date <= '{self.end_date}'
				AND account {all_accounts}
				AND is_cancelled = 0
				GROUP BY party, account	
				HAVING saldo > 0		
		""", as_dict=1)
		
		if len(dr) > 0:

			try:

				je = frappe.new_doc('Journal Entry')
				je.naming_series = self.naming_series
				je.posting_date = self.fecha_contabilizacion
				je.voucher_type = 'Period Closing Voucher'
				je.finance_book = self.libro
				je.status = 'Draft'
				je.docstatus = 0

				for r in dr:
					
					if r.saldo > 0: 
						
						#Debito
						je.append('accounts', {
							'account': self.cuenta_contrapartida,
							'debit_in_account_currency': abs(r.saldo),
							'party_type': 'Supplier',
							'party': frappe.get_doc('Supplier', r.tercero_contrapartida).name
						})
						#Credito
						je.append('accounts', {
							'account': r.account,
							'credit_in_account_currency': abs(r.saldo),
							'party_type': r.party_type,
							'party': r.party
						})

					if r.saldo < 0: 
						#Debito
						je.append('accounts', {
							'account': r.account,
							'debit_in_account_currency': abs(r.saldo),
							'party_type': r.party_type,
							'party': r.party
						})
						#Credito
						je.append('accounts', {
							'account': self.cuenta_contrapartida,
							'credit_in_account_currency': abs(r.saldo),
							'party_type': 'Supplier',
							'party': r.tercero_contrapartida
						})

				if len(je.accounts) > 0:
					je.flags.ignore_mandatory = True
					je.save()
				
				jepc = frappe.new_doc('Journal Entry Closing Account')
				jepc.parent = self.name
				jepc.parenttype = 'Cierre de Impuestos'
				jepc.parentfield = 'asientos_contables_generados'
				jepc.journal_entry = je.name
				jepc.start_date = self.start_date
				jepc.end_date = self.end_date
				jepc.flags.ignore_mandatory = True
				jepc.save()
				
				return {'success':True, 'journal':je.name}

			except Exception as ex:
				frappe.log_error(message=frappe.get_traceback(), title="qp_provisions")
				frappe.db.rollback()
	

		return {'success':False, 'journal':None}
	

# // For In Condition
# "filters": {
# 		"module": ["in", ["CRM","Selling"]]
# 	}

# // For Equal Condition
# "filters": {
# 		"module": ["=", "CRM"],
# 		"report_type": ["=", "Query Report"]
# 	}

# // For Like Condition
# "filters": {
# 		"module": ["like", "%CRM%"]
# 	}
