"""Decide whether the coordinator should consider the next authorized round."""


def next_action(policy, observed_rounds, review):
    """Use a verified Native round list and the current accepted evidence summary.

    A next-round decision is advisory to the original Native admission control.
    The caller reads the closed session, both packages and the actual test
    reports before passing their evidence state.
    """
    limit = policy["maximum_rounds"]
    if type(limit) is not int or limit < 1:
        raise ValueError("the training request must state a positive round limit")
    expected_rounds = [f"R{number:02d}" for number in range(1, len(observed_rounds) + 1)]
    if list(observed_rounds) != expected_rounds or len(expected_rounds) > limit:
        raise ValueError("the observed rounds differ from the authorized sequence")
    if not expected_rounds or review is None:
        return "await-current-round"
    if review["round"] != expected_rounds[-1]:
        raise ValueError("review must refer to the current Native round")
    if not (review["session_closed"] and review["independent_judgments_read_back"]
            and review["complete_tool_and_knowledge_verified"] and review["regression_read_back"]):
        return "await-current-round"
    if review["goals"] == "met":
        return "stop-goals-met"
    if len(expected_rounds) == limit:
        return "stop-round-limit"
    if review["goals"] != "not-met":
        return "await-goal-verdict"
    return "consider-next-round"
