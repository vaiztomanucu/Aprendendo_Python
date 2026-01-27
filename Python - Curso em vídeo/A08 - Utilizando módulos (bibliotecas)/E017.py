#Como eu tentei fazer:
co=float(input('Comprimento do cateto oposto: '))
ca=float(input('Comprimento do cateto adjacente: '))
'''print(f'A hipotenusa vai medir ...')'''

#Como ele ensinou:
'''hi=(co**2+ca**2)**(1/2)
print(f'A hipotenusa vai medir {hi:.2f}.')'''
import math
hi=math.hypot(co, ca)
print(f'A hipotenusa vai medir {hi:.2f}.')
