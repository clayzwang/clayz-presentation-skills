"""Financial layout capacity and signed cash-bridge checks, without font shrink."""
from decimal import Decimal
def table_capacity(table_top, explanation_height, *, footer_top=6.75, gap=.30):
    capacity=footer_top-table_top-explanation_height-gap
    if capacity<=0: raise ValueError('No table capacity; revise pagination')
    return capacity
def cash_bridge(flows, reported_change):
    values=[Decimal(str(v)) for v in flows]
    actual=sum(values,Decimal(0));expected=Decimal(str(reported_change))
    if actual!=expected: raise ValueError(f'Cash bridge does not reconcile: {actual} != {expected}')
    return {'computed_change':str(actual),'reported_change':str(expected),'items':len(values)}
