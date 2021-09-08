from odoo import models, fields, api
from odoo.exceptions import Warning, UserError, ValidationError

class employee_contract(models.Model):
    _inherit = 'hr.contract'
    address = fields.Char()
    id_number = fields.Char()
    
    @api.constrains('id_number')
    def validate_id_number(self):
        if len(self.id_number) != 14:
            raise ValidationError('the id number is not 14 numbers')
    def wage_in_words(self):
        currency = self.currency_id
        amount_text = currency.with_context({'lang': 'ar_001'}).amount_to_text(
		self.wage)
        amount_text = str(amount_text).replace('Euros', 'جنية مصري')
        amount_text = str(amount_text).replace('Pound', 'جنية مصري')
        amount_text = str(amount_text).replace('Dollars', 'جنية مصري')
        return amount_text + ' فقط لا غير  '
    
    def get_contract_period(self):
        diff = abs(self.date_end - self.date_start).days
        years = round(diff / 365,1)
        
        return str(years) + ' سنة '
    
    def get_day(self):
        day_to_weekday = {
            '1':'الثلاثاء',
            '2':'الاربعاء',
            '3':'الخميس',
            '4':'الجمعة',
            '5':'السبت',
            '6':'الاحد',
            '0':'الاثنين',
        }
        day = self.date_start.weekday()
        return day_to_weekday[str(day)]
    
    def get_company_address(self):
        company = self.company_id
        return f'{company.street} {company.street2} {company.city}'
