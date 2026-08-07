import re

# Matches: <Input ...> ... </> (custom closing tag format in source files)
INPUT_BLOCK_RE = re.compile(r"<Input\b([^>]*)>(.*?)<(?:/Input|/)>", re.DOTALL)

# group(1)=opening tag, group(2)=inner body, group(3)=closing tag
ALLOW_CUSTOMIZE_SECTION_RE = re.compile(
    r'(<AllowCustomizeInputKey>)(.*?)(</AllowCustomizeInputKey>)',
    re.DOTALL,
)

# Captures Name attribute value from an <Input ...> tag
NAME_ATTR_RE = re.compile(r'Name="([^"]*)"')

# Matches Key="..." attributes
KEY_ATTR_RE = re.compile(r'Key="([^"]*)"')

# Matches Time="..." attributes
TIME_ATTR_RE = re.compile(r'\bTime="[^"]*"')

# group(1)=prefix up to Key=", group(2)=space-separated key tokens, group(3)=closing quote
KEYBOARD_MOUSE_KEY_RE = re.compile(r'(<KeyboardMouse\b[^>]*\bKey=")([^"]*)(")')

# Matches one KeyboardMouse tag in an Input block body
KEYBOARD_MOUSE_TAG_RE = re.compile(r"<KeyboardMouse\b[^>]*?/?>")

# group(1)=prefix up to Key=", group(2)=OverrideKey1|OverrideKey2, group(3)=existing key value, group(4)=closing quote
ROLL_EVADE_OVERRIDE_KEY_RE = re.compile(
    r'(<KeyboardMouse\b(?=[^>]*\bName="(OverrideKey1|OverrideKey2)")(?=[^>]*\bKey=")[^>]*\bKey=")([^"]*)(")'
)


__all__ = [
    "ALLOW_CUSTOMIZE_SECTION_RE",
    "INPUT_BLOCK_RE",
    "KEY_ATTR_RE",
    "KEYBOARD_MOUSE_KEY_RE",
    "KEYBOARD_MOUSE_TAG_RE",
    "NAME_ATTR_RE",
    "ROLL_EVADE_OVERRIDE_KEY_RE",
    "TIME_ATTR_RE",
]
