# Copyright (c) 2025, Henderson Villegas and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
from frappe import _


class Provisiones(Document):
	
	@frappe.whitelist()
	def create_journal_entry(self):

		all_accounts = []

		for c in self.cuentas:
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
			SELECT t.party, t.party_type, SUM(t.saldo) as saldo, SUM(t.saldo_porc) as saldo_porc
			FROM (
				SELECT 	party, 
					party_type, 
					account, 
					ABS(SUM(credit) - SUM(debit)) as saldo, 
					{self.porcentaje} as porcentaje,
					(ABS(SUM(credit) - SUM(debit)) * {self.porcentaje}) / 100 as saldo_porc
				FROM `tabGL Entry`	
				WHERE posting_date >= '{self.start_date}'
				AND posting_date <= '{self.end_date}'
				AND account {all_accounts}
				AND is_cancelled = 0
				GROUP BY party, account, cost_center
				HAVING saldo > 0
			) as t
			GROUP BY t.party;		
		""", as_dict=1)
		
		frappe.log_error(message=dr, title="qp_provisions")

		if len(dr) > 0:

			try:

				je = frappe.new_doc('Journal Entry')
				je.naming_series = self.naming_series
				je.posting_date = self.fecha_de_asiento
				je.voucher_type = 'Journal Entry'
				je.finance_book = self.libro
				je.status = 'Submitted'
				je.docstatus = 1
				je.accounts = []

				for r in dr:

					#Debito
					if frappe.db.exists(r.party_type, {"name": r.party, "disabled":0}):
						je.append('accounts', {
							'account': self.cuenta_debito,
							'debit_in_account_currency': r.saldo_porc,
							'party_type': r.party_type,
							'party': frappe.get_doc(r.party_type, r.party).name
						})
						#Credito
						je.append('accounts', {
							'account': self.cuenta_credito,
							'credit_in_account_currency': r.saldo_porc,
							'party_type': r.party_type,
							'party': frappe.get_doc(r.party_type, r.party).name
						})

				if len(je.accounts) > 0:
					je.flags.ignore_mandatory = True
					je.save()
				
					jepc = frappe.new_doc('Journal Entry Provisions Cesantias')
					jepc.parent = self.name
					jepc.parenttype = 'Provisiones'
					jepc.parentfield = 'asientos_contables_generados'
					jepc.journal_entry = je.name
					jepc.start_date = self.start_date
					jepc.end_date = self.end_date
					jepc.flags.ignore_mandatory = True
					jepc.save()
					
					return {'success':True, 'journal':je.name}
				
				else:

					return {'success':False, 'journal':None}

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