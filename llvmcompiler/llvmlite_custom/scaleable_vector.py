from llvmlite import ir

class ScaleableVectorType(ir.VectorType):
    """
    The type for scalable vectors of primitive data items (e.g. "<vscale x f32 x 4>").
    """
    def _to_string(self):
        return "<vscale x %d x %s>" % (self.count, self.element)