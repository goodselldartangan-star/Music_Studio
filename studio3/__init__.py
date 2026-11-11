"""Music Studio 3: independent composition, synthesis, mixing and delivery modules."""
from .spec import Settings
from .composition import create_score
__all__=['Settings','create_score']
