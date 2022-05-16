def foreRGB(r: int, g: int, b: int) -> str:
   return "\x1b[38;2;" + str(r) + ";" + str(g) + ";" + str(b) + "m"

def backRGB(r: int, g: int, b: int) -> str:
   return "\x1b[48;2;" + str(r) + ";" + str(g) + ";" + str(b) + "m"