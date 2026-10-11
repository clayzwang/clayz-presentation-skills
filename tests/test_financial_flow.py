import unittest
from packages.layout.financial_flow import cash_bridge,table_capacity
class CashFlowTests(unittest.TestCase):
 def test_real_amazon_bridge(self):
  self.assertEqual(cash_bridge(['71.419','-143.457','62.913','-0.054'],'-9.179')['computed_change'],'-9.179')
 def test_sign_error_is_not_accepted(self):
  with self.assertRaises(ValueError):cash_bridge(['71.419','143.457','62.913','-0.054'],'-9.179')
 def test_explanation_consumes_available_space(self):
  self.assertLess(table_capacity(2.2,1.2),table_capacity(2.2,0))
if __name__=='__main__':unittest.main()
