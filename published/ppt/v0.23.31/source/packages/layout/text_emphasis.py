"""Project Art-selected emphasis spans onto exact manually wrapped lines.

Offsets use Python Unicode character indices in one logical paragraph. Call
separately for each authored paragraph. This helper chooses neither emphasis
nor line breaks and must not normalize or repair text to make it match.
"""


def project_emphasis(text, lines, spans):
    """Return per-line runs with text, emphasis, and source start/end offsets.

``spans`` contains half-open source intervals selected by the author. A phrase
crossing a visual line retains emphasis on both fragments. Explicit offsets
also let the author distinguish repeated occurrences of the same words.
    """
    if not isinstance(text, str) or not isinstance(lines, (list, tuple)):
        raise ValueError('Expected paragraph text and an ordered line sequence')
    if not all(isinstance(line, str) for line in lines):
        raise ValueError('Every rendered line must be text')
    if ''.join(lines) != text:
        raise ValueError('Wrapped lines must preserve the exact paragraph text')
    intervals = []
    for span in spans:
        if not isinstance(span, (list, tuple)) or len(span) != 2:
            raise ValueError('Each emphasis span must contain start and end')
        start, end = span
        if type(start) is not int or type(end) is not int:
            raise ValueError('Emphasis offsets must be integer character indices')
        if not 0 <= start < end <= len(text):
            raise ValueError('Emphasis span is outside the paragraph')
        intervals.append((start, end))

    output = []
    offset = 0
    for line in lines:
        line_end = offset + len(line)
        cuts = {offset, line_end}
        for start, end in intervals:
            if start < line_end and end > offset:
                cuts.update((max(start, offset), min(end, line_end)))
        cuts = sorted(cuts)
        runs = []
        for start, end in zip(cuts, cuts[1:]):
            emphasis = any(left <= start and end <= right
                           for left, right in intervals)
            part = text[start:end]
            if runs and runs[-1]['emphasis'] == emphasis:
                runs[-1]['text'] += part
                runs[-1]['end'] = end
            else:
                runs.append(dict(text=part, emphasis=emphasis,
                                 start=start, end=end))
        output.append(runs)
        offset = line_end
    return output
