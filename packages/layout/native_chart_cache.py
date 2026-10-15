"""Optional, value-preserving numeric-cache spelling for native charts.

This operates on existing category-series numRef caches. It does not choose a
unit, parse Excel number formats, edit a workbook, or create text data labels.
Native selectors, displayed labels and target-app behavior need separate checks.
"""
from decimal import Decimal, InvalidOperation

_CHART_NS = '{http://schemas.openxmlformats.org/drawingml/2006/chart}'


def format_numeric_cache(chart, decimals, *, signed=False):
    """Spell existing cached numbers at an explicit precision without rounding.

    Validate every target before changing any of them. A requested precision
    that would change even one numeric value is rejected atomically. Pass a
    python-pptx Chart and the intended decimal count; percent scaling and all
    other display conventions remain the author's responsibility.
    """
    if type(decimals) is not int or decimals < 0:
        raise ValueError('decimals must be a nonnegative integer')
    if type(signed) is not bool:
        raise ValueError('signed must be a boolean')
    root = getattr(chart, '_chartSpace', None)
    if root is None:
        raise TypeError('Pass a python-pptx Chart')
    targets = list(root.xpath('.//c:ser/c:val/c:numRef/c:numCache/c:pt/c:v'))
    pending = []
    spec = ('+' if signed else '') + '.' + str(decimals) + 'f'
    for target in targets:
        before = target.text
        try:
            value = Decimal(before)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError('Cache contains a nonnumeric value') from exc
        if not value.is_finite():
            raise ValueError('Cache contains a nonfinite value')
        after = format(value, spec)
        if Decimal(after) != value:
            raise ValueError('Requested precision would change a cached value')
        # c:v can be a generic lxml element without python-pptx's XPath map.
        series = next(target.iterancestors(_CHART_NS + 'ser'))
        index = series.find(_CHART_NS + 'idx')
        pending.append((target, {
            'series_index': index.get('val') if index is not None else None,
            'point_index': target.getparent().get('idx'),
            'before': before, 'after': after,
        }))
    for target, item in pending:
        target.text = item['after']
    return {
        'decimals': decimals, 'signed': signed,
        'cache_values_checked': len(pending),
        'lexemes_changed': sum(item['before'] != item['after'] for _, item in pending),
        'numeric_values_changed': 0,
        'values': [item for _, item in pending],
        'scope': 'Existing numRef value caches only; no workbook, formula, '
                 'label-text, selector, number-format or rendering acceptance.',
    }
