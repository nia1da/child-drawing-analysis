"""Tek giriş noktası: bir sayfa görüntüsünden önişleme, maskeler, satırlar ve özellikler."""
from dataclasses import dataclass

from .features import extract_features, quality_flags
from .masks import Masks, build_masks, pen_info
from .normalize import Preprocessed, preprocess
from .paths import HW_VERSION
from .segment import Segmentation, segment_lines


@dataclass
class Result:
    pre: Preprocessed
    masks: Masks
    seg: Segmentation
    features: dict
    quality: dict
    version: str = HW_VERSION


def analyze_page(rgb, dpi, overlay_boxes=None):
    """rgb (H,W,3 uint8, A4 sayfa), dpi (piksel/inç), overlay_boxes [(x0,y0,x1,y1)] orijinal piksel: PDF metin katmanındaki kelime kutuları (XXX, telif satırı)."""
    pre = preprocess(rgb, dpi, overlay_boxes)
    masks = build_masks(pre)
    seg = segment_lines(masks, min_line_px=max(6, int(2.0 / pre.mm_per_px ** 2)))  # ≥ 2 mm² mürekkep
    features = extract_features(pre, masks, seg)
    quality = quality_flags(pre, masks, pen_info(pre, masks.hw))
    return Result(pre, masks, seg, features, quality)
