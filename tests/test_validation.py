import unittest
from published import validate_menu
class Validation(unittest.TestCase):
 def menu(self):return {'name':'Shop','currency':'VND','items':[{'name':'Tea','price':''}]}
 def test_optional_price(self):self.assertEqual(validate_menu(self.menu())['items'][0]['price'],'')
 def test_script_image_rejected(self):
  m=self.menu();m['items'][0]['image']='javascript:alert(1)'
  with self.assertRaises(ValueError):validate_menu(m)
 def test_negative_price_rejected(self):
  m=self.menu();m['items'][0]['price']='-5'
  with self.assertRaises(ValueError):validate_menu(m)
 def test_item_limit(self):
  m=self.menu();m['items']*=31
  with self.assertRaises(ValueError):validate_menu(m)
