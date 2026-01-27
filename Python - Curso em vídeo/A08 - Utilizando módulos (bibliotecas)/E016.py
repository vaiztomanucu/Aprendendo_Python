#Como eu tentei fazer:
'''v=float(input('Digite um valor: '))
print(f'O valor digitado foi {v} e sua porção inteira é {v:.0f}.')'''

#Como ele ensinou:
from math import trunc
v1=float(input('Digite um valor: '))
print(f'O valor digitado foi {v1} e sua porção inteira é {trunc(v1)}.')
print(f'O valor digitado foi {v1} e sua porção inteira é {int(v1)}.')
