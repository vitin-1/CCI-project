import sys
from unittest.mock import MagicMock

# Mock de libs que podem não estar instaladas no ambiente de teste
# ou que carregam modelos pesados em GPU/disco.

# insightface — modelo buffalo_l não é baixado nos testes
sys.modules["insightface"] = MagicMock()
sys.modules["insightface.app"] = MagicMock()

# supabase — client de cloud; não conecta em testes unitários
sys.modules["supabase"] = MagicMock()

# cv2 pode falhar em alguns ambientes de CI sem display
# Só mockamos se não estiver disponível
try:
    import cv2  # noqa: F401
except ImportError:
    sys.modules["cv2"] = MagicMock()
