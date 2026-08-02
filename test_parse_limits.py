from skills_ref.parser import read_properties

class DummyPath:
    def __init__(self, p):
        self.p = p
    # ... wait, we can't easily mock Path
