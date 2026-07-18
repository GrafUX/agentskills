from dataclasses import dataclass, field
@dataclass
class A:
    m: dict = field(default_factory=dict)
a = A(m=None)
print(a.m)
b = A()
print(b.m)
