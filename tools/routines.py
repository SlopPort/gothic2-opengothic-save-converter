"""Resolve original named daily routines without treating archive sentinels as code."""
import re

def routine_function(name,byname):
    if not name or name=='\xffINSTANCE_HELP':return None
    name=name.upper()
    if re.fullmatch(r'RTN_[A-Z0-9_]+',name) is None:
        raise ValueError('Unsupported source routine name')
    symbol=byname.get(name)
    if not symbol or symbol['type']!=5 or symbol['count']!=0 or symbol['flags']&12:
        raise ValueError('Source routine is not a matching internal zero-argument function')
    return name
