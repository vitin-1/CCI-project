import logging
import numpy as np
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

_model: FaceAnalysis | None = None

EMBEDDING_DIM = 512


def get_model() -> FaceAnalysis:
    global _model
    if _model is None:
        logger.info("loading_insightface_model model=buffalo_l")
        _model = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        _model.prepare(ctx_id=0, det_size=(640, 640))
    return _model


def normalize(embedding: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(embedding)
    if norm == 0.0:
        return embedding
    return embedding / norm


def detect_faces(image: np.ndarray) -> list[dict]:
    """
    Detecta todos os rostos em `image` (BGR numpy array).
    Retorna lista de {"embedding": np.ndarray (normalizado, 512-d), "bbox": dict}.
    Nunca lança exceção — rostos com falha são logados e descartados.
    """
    model = get_model()
    try:
        raw_faces = model.get(image)
    except Exception:
        logger.exception("insightface_inference_failed shape=%s", image.shape)
        return []

    results: list[dict] = []
    for face in raw_faces:
        try:
            x1, y1, x2, y2 = face.bbox.astype(int).tolist()
            results.append({
                "embedding": normalize(face.embedding.astype(np.float32)),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            })
        except Exception:
            logger.exception("face_parse_failed")

    return results


def extract_largest_face_embedding(image: np.ndarray) -> np.ndarray | None:
    """
    Retorna o embedding do maior rosto detectado em `image`.
    Usado para selfies de busca — um único rosto é suficiente.
    Retorna None se nenhum rosto for detectado.
    """
    faces = detect_faces(image)
    if not faces:
        return None
    best = max(
        faces,
        key=lambda f: (f["bbox"]["x2"] - f["bbox"]["x1"]) * (f["bbox"]["y2"] - f["bbox"]["y1"]),
    )
    return best["embedding"]
