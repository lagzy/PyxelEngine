"""
Event Sheet Processor — Runtime executor for event sheet logic.

Iterates over all event blocks each tick: if every condition in a block
evaluates to True, all actions in that block are executed.
"""

import sys


class EventBlockData:
    """Pure-data container for one event row (conditions + actions)."""

    def __init__(self):
        self.conditions = []  # list of Condition instances
        self.actions = []     # list of Action instances

    def to_dict(self):
        return {
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions]
        }

    @staticmethod
    def from_dict(data):
        from engine.core.event_system import Condition, Action
        block = EventBlockData()
        for c_data in data.get("conditions", []):
            cond = Condition.from_dict(c_data)
            if cond:
                block.conditions.append(cond)
        for a_data in data.get("actions", []):
            act = Action.from_dict(a_data)
            if act:
                block.actions.append(act)
        return block


class EventSheetProcessor:
    """Evaluates and executes event blocks during gameplay."""

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.event_blocks = []  # list of EventBlockData

    def add_block(self, block_data):
        """Register a new EventBlockData for processing."""
        self.event_blocks.append(block_data)

    def remove_block(self, block_data):
        """Unregister an EventBlockData."""
        if block_data in self.event_blocks:
            self.event_blocks.remove(block_data)

    def update(self, dt):
        """Called every tick while the engine state is PLAYING.

        For each block, evaluate all conditions.  If every condition
        returns True, execute every action in the block.
        """
        for block in self.event_blocks:
            # Skip blocks with no conditions — nothing can trigger them
            if not block.conditions:
                continue

            all_met = all(cond.evaluate(dt) for cond in block.conditions)
            if all_met:
                for action in block.actions:
                    try:
                        action.execute()
                    except Exception as exc:
                        sys.stderr.write(
                            f"[EventSheetProcessor] Action error: {exc}\n"
                        )
