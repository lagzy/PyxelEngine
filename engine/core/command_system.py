"""
Command System — Implementation of the Command pattern for Undo/Redo functionality.
"""

class Command:
    """Base class for all undoable editor commands."""
    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

class CommandHistory:
    """Manages the undo and redo stacks."""
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50

    def execute(self, command):
        """Execute a new command and add it to the undo stack."""
        try:
            command.execute()
            self.undo_stack.append(command)
            self.redo_stack.clear()
            
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
        except Exception as e:
            import traceback
            print(f"Error executing command: {e}")
            traceback.print_exc()

    def undo(self):
        """Undo the last command."""
        if not self.undo_stack:
            print("Nothing to undo")
            return
        
        command = self.undo_stack.pop()
        try:
            command.undo()
            self.redo_stack.append(command)
        except Exception as e:
            print(f"Error undoing command: {e}")

    def redo(self):
        """Redo the last undone command."""
        if not self.redo_stack:
            print("Nothing to redo")
            return
            
        command = self.redo_stack.pop()
        try:
            command.execute()
            self.undo_stack.append(command)
        except Exception as e:
            print(f"Error redoing command: {e}")

# Global instance
history = CommandHistory()
