#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['ShipmentOut']
__metaclass__ = PoolMeta


class ShipmentOut:
    __name__ = 'stock.shipment.out'
    carrier = fields.Many2One('carrier', 'Carrier', states={
            'readonly': Eval('state') != 'draft',
            }, on_change=['carrier'],
        depends=['state'])
    cost_currency = fields.Many2One('currency.currency',
            'Cost Currency', states={
            'invisible': ~Eval('carrier'),
            'required': Bool(Eval('carrier')),
            'readonly': ~Eval('state').in_(['draft', 'waiting', 'assigned',
                    'packed']),
            }, depends=['carrier', 'state'])
    cost_currency_digits = fields.Function(fields.Integer(
        'Cost Currency Digits', on_change_with=['currency']),
        'on_change_with_cost_currency_digits')
    cost = fields.Numeric('Cost',
            digits=(16, Eval('cost_currency_digits', 2)), states={
            'invisible': ~Eval('carrier'),
            'readonly': ~Eval('state').in_(['draft', 'waiting', 'assigned',
                    'packed']),
            }, depends=['carrier', 'state', 'cost_currency_digits'])
    cost_invoice_line = fields.Many2One('account.invoice.line',
            'Cost Invoice Line', readonly=True)

    @classmethod
    def __setup__(cls):
        super(ShipmentOut, cls).__setup__()
        cls._error_messages.update({
                'missing_account_revenue': ('Missing "Account Revenue" on '
                    'product "%s".'),
                })
        if not cls.inventory_moves.on_change:
            cls.inventory_moves.on_change = []
        for fname in ('carrier', 'customer', 'inventory_moves'):
            if fname not in cls.inventory_moves.on_change:
                cls.inventory_moves.on_change.append(fname)
        for fname in cls.inventory_moves.on_change:
            if fname not in cls.carrier.on_change:
                cls.carrier.on_change.append(fname)

    def on_change_with_cost_currency_digits(self, name=None):
        if self.cost_currency:
            return self.cost_currency.digits
        return 2

    def _get_carrier_context(self):
        return {}

    def get_carrier_context(self):
        return self._get_carrier_context()

    def on_change_carrier(self):
        return self.on_change_inventory_moves()

    def on_change_inventory_moves(self):
        Currency = Pool().get('currency.currency')

        try:
            result = super(ShipmentOut, self).on_change_inventory_moves()
        except AttributeError:
            result = {}
        if not self.carrier:
            return result
        with Transaction().set_context(self._get_carrier_context()):
            cost, currency_id = self.carrier.get_sale_price()
        currency = Currency(currency_id)
        result['cost'] = cost
        result['cost_currency'] = currency.id
        result['cost_currency_digits'] = currency.digits if currency else 2
        return result

    def _get_cost_tax_rule_pattern(self):
        'Get tax rule pattern for invoice line'
        return {}

    def get_cost_invoice_line(self, invoice):
        pool = Pool()
        Product = pool.get('product.product')
        Currency = pool.get('currency.currency')
        InvoiceLine = pool.get('account.invoice.line')

        if not self.cost:
            return {}
        with Transaction().set_user(0, set_context=True):
            invoice_line = InvoiceLine()
        product = self.carrier.carrier_product
        invoice_line.type = 'line'

        party = invoice.party
        party_context = {}
        if party.lang:
            party_context['language'] = party.lang.code
        with Transaction().set_context(party_context):
            invoice_line.description = Product(product.id).rec_name

        invoice_line.quantity = 1  # XXX
        invoice_line.unit = product.sale_uom.id
        cost = self.cost
        if invoice.currency != self.cost_currency:
            with Transaction().set_context(date=invoice.currency_date):
                cost = Currency.compute(self.cost_currency, cost,
                    invoice.currency)
        invoice_line.unit_price = cost

        taxes = []
        pattern = self._get_cost_tax_rule_pattern()
        for tax in product.customer_taxes_used:
            if party.customer_tax_rule:
                tax_ids = party.customer_tax_rule.apply(None, pattern)
                if tax_ids:
                    taxes.extend(tax_ids)
                continue
            taxes.append(tax.id)
        invoice_line.taxes = taxes

        invoice_line.account = product.account_revenue_used
        if not invoice_line.account:
            self.raise_user_error('missing_account_revenue',
                    error_args=(product.rec_name,))
        return invoice_line
