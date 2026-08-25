import sys
from unittest.mock import MagicMock

# Mock insightface antes de qualquer import — permite rodar test_detector.py
# sem a lib instalada. Os testes já mockam o modelo internamente via @patch.
sys.modules["insightface"] = MagicMock()
sys.modules["insightface.app"] = MagicMock()
