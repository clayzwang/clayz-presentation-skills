"""Compare stated measurement boundaries without assuming unknown scopes match."""


def compare(left, right, dimensions):
    """Return a reading observation across caller-selected dimensions.

    Values come from the current evidence, expressed in the same vocabulary.
    An omitted or None value is unknown. The caller supplies the significant
    dimensions for the actual comparison. This helper does not certify claims,
    fill missing evidence or block a stage.
    """
    dimensions = tuple(dimensions)
    if not dimensions or len(dimensions) != len(set(dimensions)):
        raise ValueError("supply distinct relevant dimension names")
    same = []
    different = []
    unknown = []
    for dimension in dimensions:
        a = left.get(dimension)
        b = right.get(dimension)
        if a is None or b is None:
            unknown.append(dimension)
        elif a == b:
            same.append(dimension)
        else:
            different.append(dimension)
    return {"matching": same, "different": different, "unknown": unknown,
            "establishes_same_scope": not (different or unknown)}
