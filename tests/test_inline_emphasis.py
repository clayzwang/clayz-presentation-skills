import pathlib,json,unittest
from packages.layout.inline_emphasis import segments,validate_tokens
class EmphasisRegression(unittest.TestCase):
 def test_actual_apple_balance_preserves_copy_and_selects_values(self):
  t=json.loads((pathlib.Path(__file__).parent/'fixtures/apple-balance-text.json').read_text())['text'];r=segments(t,['39.544','146.517'])
  self.assertEqual(''.join(x for x,b in r),t);self.assertEqual([x for x,b in r if b],['146.517','39.544','146.517'])
 def test_partial_numeric_token_is_rejected(self):
  with self.assertRaises(ValueError):validate_tokens('余额146.517',['46.517'])
if __name__=='__main__':unittest.main()
