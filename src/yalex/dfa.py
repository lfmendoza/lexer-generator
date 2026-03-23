"""DFA: subset construction and minimization."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from yalex.nfa import NFA, NFAState


@dataclass
class DFAState:
    id: int
    transitions: dict[int, int] = field(default_factory=dict)
    is_accept: bool = False
    rule_index: int = -1


def epsilon_closure(nfa_states: dict[int, NFAState], state_set: frozenset[int]) -> frozenset[int]:
    """Compute epsilon closure of a set of NFA states."""
    stack = list(state_set)
    closure = set(state_set)
    while stack:
        s = stack.pop()
        for t in nfa_states[s].transitions.get(None, []):
            if t not in closure:
                closure.add(t)
                stack.append(t)
    return frozenset(closure)


def move(nfa_states: dict[int, NFAState], state_set: frozenset[int], symbol: int) -> frozenset[int]:
    """Compute the set of states reachable from state_set on symbol."""
    result = set()
    for s in state_set:
        for t in nfa_states[s].transitions.get(symbol, []):
            result.add(t)
    return frozenset(result)


def nfa_to_dfa(nfa: NFA) -> tuple[dict[int, DFAState], int]:
    """Subset construction: NFA -> DFA. Returns (states_dict, start_id)."""
    all_symbols: set[int] = set()
    for state in nfa.states.values():
        for sym in state.transitions:
            if sym is not None:
                all_symbols.add(sym)

    start_closure = epsilon_closure(nfa.states, frozenset([nfa.start]))

    dfa_states: dict[int, DFAState] = {}
    state_map: dict[frozenset[int], int] = {}
    next_id = 0
    queue: deque[frozenset[int]] = deque()

    def get_or_create(nfa_set: frozenset[int]) -> int:
        nonlocal next_id
        if nfa_set in state_map:
            return state_map[nfa_set]
        sid = next_id
        next_id += 1
        state_map[nfa_set] = sid

        is_accept = False
        best_rule = -1
        for ns in nfa_set:
            ns_state = nfa.states[ns]
            if ns_state.is_accept:
                if not is_accept or ns_state.rule_index < best_rule:
                    best_rule = ns_state.rule_index
                is_accept = True

        dfa_states[sid] = DFAState(sid, {}, is_accept, best_rule)
        queue.append(nfa_set)
        return sid

    start_id = get_or_create(start_closure)

    while queue:
        current_nfa_set = queue.popleft()
        current_dfa_id = state_map[current_nfa_set]

        for sym in all_symbols:
            moved = move(nfa.states, current_nfa_set, sym)
            if not moved:
                continue
            closed = epsilon_closure(nfa.states, moved)
            if not closed:
                continue
            target_id = get_or_create(closed)
            dfa_states[current_dfa_id].transitions[sym] = target_id

    return dfa_states, start_id


def minimize_dfa(
    dfa_states: dict[int, DFAState], start_id: int
) -> tuple[dict[int, DFAState], int]:
    """Minimize a DFA using partition refinement."""
    if not dfa_states:
        return dfa_states, start_id

    all_symbols: set[int] = set()
    for s in dfa_states.values():
        all_symbols.update(s.transitions.keys())

    groups: dict[tuple[bool, int], set[int]] = defaultdict(set)
    for sid, state in dfa_states.items():
        key = (state.is_accept, state.rule_index)
        groups[key].add(sid)

    partition = list(groups.values())

    def find_group(state_id: int) -> int:
        for i, group in enumerate(partition):
            if state_id in group:
                return i
        return -1

    changed = True
    while changed:
        changed = False
        new_partition = []
        for group in partition:
            if len(group) <= 1:
                new_partition.append(group)
                continue
            splits: dict[tuple, set[int]] = defaultdict(set)
            for sid in group:
                sig = []
                for sym in sorted(all_symbols):
                    target = dfa_states[sid].transitions.get(sym, -1)
                    tg = find_group(target) if target != -1 else -1
                    sig.append(tg)
                splits[tuple(sig)].add(sid)
            if len(splits) > 1:
                changed = True
                new_partition.extend(splits.values())
            else:
                new_partition.append(group)
        partition = new_partition

    group_of: dict[int, int] = {}
    for i, group in enumerate(partition):
        for sid in group:
            group_of[sid] = i

    new_states: dict[int, DFAState] = {}
    for i, group in enumerate(partition):
        rep = next(iter(group))
        old_state = dfa_states[rep]
        new_trans = {}
        for sym, target in old_state.transitions.items():
            new_trans[sym] = group_of[target]
        new_states[i] = DFAState(i, new_trans, old_state.is_accept, old_state.rule_index)

    new_start = group_of[start_id]
    return new_states, new_start
