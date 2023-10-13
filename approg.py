"""
tests
"""

import os
import sys
up = os.path.normpath(os.path.join(os.getcwd(), "../src"))
#sys.path.append(up)
#sys.path.append(os.getcwd())

from awkish import Awk


awk = Awk()
awk.when(True)(lambda f1='', f2='':print(f2+','+f1))
