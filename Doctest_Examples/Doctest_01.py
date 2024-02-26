# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 15:11:06 2020

@author: eessrp
"""

def square(x):
    """Return the square of x.
    :param x: the value to be squared, or anything with the * operator defined
    :type x: real, int, complex or other
    :return: the square of x
    :rtype: the same type as the paramerter 
    """
    return x * x

xvalue=2.1
y = square(xvalue)    
print("(%g)^2=%g"%(xvalue,y))

ok=( y==(xvalue*xvalue) )
if ok:
    print("Square worked")
else:
    print("Square failed")
    