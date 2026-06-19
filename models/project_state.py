from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProjectState:
    current_visible_mip: int = 0
    image_path: Optional[str] = None
    save_path: Optional[str] = None
    save_project_name: Optional[str] = None
    loading_project: bool = False
    max_mip_level: int = 0
    mip_slider_buffer: Optional[dict] = None
    self_mip_changes: Dict[str, int] = field(default_factory=dict)
    mips: List = field(default_factory=list)
    original_mips: List = field(default_factory=list)
    show_r: bool = True
    show_g: bool = True
    show_b: bool = True
    show_a: bool = True
    preview_background_mode: str = "solid"
    uv_weight_map = None
