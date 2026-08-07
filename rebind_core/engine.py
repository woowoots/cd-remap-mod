from .models import RebindConfig, SourceFile
from .parser import patch_allow_customize
from .transformer import process_text


def generate_rebind_outputs(
    inputmap_path: str,
    inputmap_common_path: str,
    key_values: dict[str, str],
) -> tuple[str, str]:
    config = RebindConfig(key_values=dict(key_values))

    with open(inputmap_path, "r", encoding="utf-8") as f:
        inputmap_text = f.read()
    with open(inputmap_common_path, "r", encoding="utf-8") as f:
        inputmap_common_text = f.read()

    out_inputmap = process_text(inputmap_text, config, SourceFile.INPUTMAP)
    out_inputmap = patch_allow_customize(out_inputmap)

    out_inputmap_common = process_text(inputmap_common_text, config, SourceFile.INPUTMAP_COMMON)
    return out_inputmap, out_inputmap_common
