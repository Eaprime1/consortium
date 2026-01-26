#!/usr/bin/env python3
"""
Nani Decision Engine - Core autonomic decision layer
Load → Do → Unload optimization pattern
"""

import random
import json
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field


class DecisionState(Enum):
    """Core decision states"""
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"
    WAIT = "wait"


@dataclass
class DecisionContext:
    """Context for decision evaluation"""
    operation: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)
    history: list = field(default_factory=list)


class NaniDecisionEngine:
    """
    Triadic decision engine with learning capability

    Operates in three modes:
    1. Random (initial) - Random weighted decisions
    2. Pattern (learning) - Pattern recognition from history
    3. Autonomous (mature) - Self-directed decisions
    """

    def __init__(self, entity_name: str, mode: str = "random"):
        self.entity_name = entity_name
        self.mode = mode  # random, pattern, autonomous
        self.decision_history = []
        self.pattern_weights = {
            DecisionState.YES: 0.4,
            DecisionState.NO: 0.2,
            DecisionState.MAYBE: 0.3,
            DecisionState.WAIT: 0.1
        }

    def decide(self, context: DecisionContext) -> DecisionState:
        """
        Make a decision based on current mode

        Load → Do → Unload pattern:
        - Load: Context evaluation
        - Do: Decision execution
        - Unload: Result recording
        """
        # LOAD
        decision = self._evaluate(context)

        # DO (record)
        self._record_decision(context, decision)

        # UNLOAD (return)
        return decision

    def _evaluate(self, context: DecisionContext) -> DecisionState:
        """Evaluate decision based on mode"""
        if self.mode == "random":
            return self._random_decision()
        elif self.mode == "pattern":
            return self._pattern_decision(context)
        elif self.mode == "autonomous":
            return self._autonomous_decision(context)
        else:
            return DecisionState.MAYBE

    def _random_decision(self) -> DecisionState:
        """Weighted random decision (initial learning phase)"""
        states = list(DecisionState)
        weights = [self.pattern_weights[s] for s in states]
        return random.choices(states, weights=weights)[0]

    def _pattern_decision(self, context: DecisionContext) -> DecisionState:
        """Pattern-based decision (learning phase)"""
        # Look for similar contexts in history
        similar_contexts = [
            h for h in self.decision_history
            if h['context'].operation == context.operation
        ]

        if not similar_contexts:
            return self._random_decision()

        # Find most common successful decision
        decision_counts = {}
        for h in similar_contexts[-10:]:  # Last 10 similar
            dec = h['decision']
            decision_counts[dec] = decision_counts.get(dec, 0) + 1

        if decision_counts:
            return max(decision_counts, key=decision_counts.get)

        return self._random_decision()

    def _autonomous_decision(self, context: DecisionContext) -> DecisionState:
        """Fully autonomous decision (mature phase)"""
        # Custom decision logic per entity
        # This would be overridden by specific command entities
        return self._pattern_decision(context)

    def _record_decision(self, context: DecisionContext, decision: DecisionState):
        """Record decision for learning"""
        self.decision_history.append({
            'context': context,
            'decision': decision,
            'mode': self.mode
        })

        # Update weights based on outcomes (simple learning)
        if len(self.decision_history) > 10:
            self._update_weights()

    def _update_weights(self):
        """Update decision weights based on history"""
        recent = self.decision_history[-20:]

        for state in DecisionState:
            count = sum(1 for h in recent if h['decision'] == state)
            # Gradually adjust weights toward observed frequencies
            observed_freq = count / len(recent)
            current_weight = self.pattern_weights[state]
            # Lerp toward observed
            self.pattern_weights[state] = current_weight * 0.9 + observed_freq * 0.1

        # Normalize
        total = sum(self.pattern_weights.values())
        for state in DecisionState:
            self.pattern_weights[state] /= total

    def evolve(self):
        """Evolve to next mode if ready"""
        if self.mode == "random" and len(self.decision_history) > 50:
            self.mode = "pattern"
            print(f"[{self.entity_name}] Evolved to PATTERN mode")
        elif self.mode == "pattern" and len(self.decision_history) > 200:
            self.mode = "autonomous"
            print(f"[{self.entity_name}] Evolved to AUTONOMOUS mode")


class NaniCommandEntity:
    """
    Base class for command entities

    Each command (pwd, ls, cd, etc.) extends this
    """

    def __init__(self, command_name: str):
        self.command_name = command_name
        self.engine = NaniDecisionEngine(command_name)
        self.loaded = False

    def load(self, context: Dict[str, Any]):
        """LOAD phase - minimal context only"""
        self.context = context
        self.loaded = True
        return self

    def do(self) -> Any:
        """DO phase - execute operation"""
        if not self.loaded:
            raise RuntimeError("Entity not loaded")

        # Build decision context
        ctx = DecisionContext(
            operation=self.command_name,
            inputs=self.context.get('inputs', {}),
            system_state=self.context.get('system_state', {})
        )

        # Make decision
        decision = self.engine.decide(ctx)

        # Execute based on decision
        if decision == DecisionState.YES:
            result = self._execute()
        elif decision == DecisionState.NO:
            result = {"status": "declined", "reason": "decision_engine"}
        elif decision == DecisionState.MAYBE:
            result = self._maybe_execute()
        elif decision == DecisionState.WAIT:
            result = {"status": "waiting", "reason": "timing_context"}
        else:
            result = {"status": "error", "reason": "unknown_decision"}

        return result

    def unload(self) -> None:
        """UNLOAD phase - clean exit"""
        self.loaded = False
        self.context = None
        self.engine.evolve()  # Check if ready to evolve

    def _execute(self) -> Any:
        """Actual command execution - override in subclass"""
        raise NotImplementedError("Subclass must implement _execute")

    def _maybe_execute(self) -> Any:
        """Conditional execution - override if needed"""
        # Default: treat maybe as yes with caution flag
        result = self._execute()
        result['caution'] = True
        return result

    def solo_capabilities(self) -> list:
        """What this entity can do alone"""
        return []

    def system_capabilities(self) -> list:
        """What this entity can do with others"""
        return []


# Example: PWD command entity
class PwdEntity(NaniCommandEntity):
    """pwd - Print working directory"""

    def __init__(self):
        super().__init__("pwd")

    def _execute(self) -> Any:
        import os
        return {
            "status": "success",
            "command": "pwd",
            "result": os.getcwd()
        }

    def solo_capabilities(self) -> list:
        return ["print_working_directory"]

    def system_capabilities(self) -> list:
        return ["provide_context_to_cd", "validate_paths", "anchor_relative_operations"]


# Example: LS command entity
class LsEntity(NaniCommandEntity):
    """ls - List directory contents"""

    def __init__(self):
        super().__init__("ls")

    def _execute(self) -> Any:
        import os
        path = self.context.get('inputs', {}).get('path', '.')

        try:
            items = os.listdir(path)
            return {
                "status": "success",
                "command": "ls",
                "path": path,
                "result": items
            }
        except Exception as e:
            return {
                "status": "error",
                "command": "ls",
                "error": str(e)
            }

    def solo_capabilities(self) -> list:
        return ["list_directory", "count_items", "filter_patterns"]

    def system_capabilities(self) -> list:
        return [
            "provide_items_to_grep",
            "feed_find_results",
            "inventory_for_backup",
            "scan_for_rescue"
        ]


# Utility functions
def quick_execute(entity_class, context: Dict[str, Any]) -> Any:
    """
    Quick execution helper using load→do→unload pattern

    Single file transfer optimization
    """
    entity = entity_class()
    entity.load(context)
    result = entity.do()
    entity.unload()
    return result


if __name__ == "__main__":
    print("∰◊€π¿🌌∞ Nani Decision Engine Test ∰◊€π¿🌌∞\n")

    # Test PWD entity
    print("Testing PWD entity...")
    pwd_result = quick_execute(PwdEntity, {})
    print(f"  Result: {pwd_result}\n")

    # Test LS entity
    print("Testing LS entity...")
    ls_result = quick_execute(LsEntity, {'inputs': {'path': '.'}})
    print(f"  Result: {ls_result}\n")

    # Test learning
    print("Testing decision engine learning...")
    engine = NaniDecisionEngine("test_entity")
    print(f"  Initial mode: {engine.mode}")
    print(f"  Initial weights: {engine.pattern_weights}\n")

    # Simulate decisions
    for i in range(60):
        ctx = DecisionContext(operation="test", inputs={'iteration': i})
        decision = engine.decide(ctx)
        if i % 20 == 0:
            print(f"  Decision {i}: {decision.value}, Mode: {engine.mode}")

    print(f"\n  Final mode: {engine.mode}")
    print(f"  Final weights: {engine.pattern_weights}")

    print("\n🤖 Nani entities ready for deployment!")
