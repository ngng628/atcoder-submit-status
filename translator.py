import csv
import pathlib

def _read_csv(path: pathlib.Path):
   res = {}
   with open(str(path), 'r') as f:
      table = csv.reader(f, delimiter=',', doublequote=True)
      for row in table:
         res[row[0]] = row[1]
   return res

class Translator:
   def __init__(self):
      self.japanese = _read_csv('lang/ja.csv')

   def translate(self, text: str, lang: str='ja') -> str:
      if lang == 'ja':
         return self.pananese[text]
      else:
         return text