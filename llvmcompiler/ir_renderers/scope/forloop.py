from .scope import Scope

class ForLoop(Scope):
    def _define_scope_blocks(self):
        self.scope_blocks = {
            "condition": self.builder.cursor.append_basic_block(),
            "start": self.builder.cursor.append_basic_block(),
            "end": self.builder.cursor.append_basic_block()
        }

    def _exit_scope(self):
        pass