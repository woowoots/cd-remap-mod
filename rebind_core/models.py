from dataclasses import dataclass, field as dc_field
from enum import Enum

DEFAULTS = {
    "up": "w",
    "down": "s",
    "left": "a",
    "right": "d",
    "menu_left": "q",
    "menu_right": "e",
    "slot1": "q",
    "slot2": "e",
    "slot3": "r",
    "slot4": "f",
    "slot5": "t",
    "slot6": "g",
    "roll_evade_key1": "alt",
    "roll_evade_key2": "mouseX2",
    "axiom_force_hold_delay": "0.2",
    "enter_game": "a"
}
ALLOW_CUSTOMIZE_DEFAULTS = ("w", "a", "s", "d")

class ValidationType(str, Enum):
    ALLOWED_KEY = "allowed_key"
    NON_NEGATIVE_FLOAT = "non_negative_float"


class SourceFile(str, Enum):
    INPUTMAP = "inputmap"
    INPUTMAP_COMMON = "inputmap_common"


@dataclass(frozen=True)
class RuleTarget:
    source_file: SourceFile
    markers: tuple[str, ...] = ()
    ignore: bool = False


@dataclass(frozen=True)
class RuleSelector:
    tag: str = ""
    names: tuple[str, ...] = ()
    attribute: str = "Key"


def input_map(*markers: str, ignore: bool = False) -> RuleTarget:
    return RuleTarget(SourceFile.INPUTMAP, markers=markers, ignore=ignore)


def input_map_common(*markers: str, ignore: bool = False) -> RuleTarget:
    return RuleTarget(SourceFile.INPUTMAP_COMMON, markers=markers, ignore=ignore)


INPUT_GLOBAL = input_map()
COMMON_GLOBAL = input_map_common()


@dataclass(frozen=True)
class RuleSpec:
    field: str
    source_key: str = ""
    targets: tuple[RuleTarget, ...] = ()
    selector: RuleSelector = dc_field(default_factory=RuleSelector)
    validation: ValidationType = ValidationType.ALLOWED_KEY
    unique: bool = False
    primary_customize_marker: bool = False
    ui_section: str = ""
    ui_label: str = ""
    ui_width: int = 8
    ui_entry_sticky: str = ""

_SECTION_MOVEMENT = "Movement keys"
_SECTION_MENU_NAV = "Menu navigation"
_SECTION_MENU_ACTION = "Menu action keys"
_SECTION_ROLL_EVADE = "Roll/Evade"
_SECTION_ENTER_GAME = "Enter game"


_MENU_SLOT_MARKERS = ("Key_MiniGame", "Key_Housing")
_ROLL_EVADE_MARKERS = ("Key_Roll", "Key_Evade")
_ENTER_GAME_TO_MENU_MARKERS = ("ContinueTitleView2", "StartGameOffLineMode2")

_generic_global = (
    INPUT_GLOBAL, 
    COMMON_GLOBAL)
_menu_left = (
    input_map(ignore=True), 
    input_map_common("MenuMoveLeft"))
_menu_right = (
    input_map(ignore=True), 
    input_map_common("MenuMoveRight"))
_menu_slots =  (
    input_map(*_MENU_SLOT_MARKERS), 
    COMMON_GLOBAL)
_roll_evade = (
    input_map(*_ROLL_EVADE_MARKERS),
      input_map_common(ignore=True))
_axiom_timer = (
    input_map("Key_Skill_11_Start"),
      input_map_common(ignore=True))
_enter_game_to_menu = (
    input_map(ignore=True),
    input_map_common(*_ENTER_GAME_TO_MENU_MARKERS),
)

_key_selector = RuleSelector(attribute="Key")
_override_selector_1 = RuleSelector(tag="KeyboardMouse", names=("OverrideKey1",), attribute="Key")
_override_selector_2 = RuleSelector(tag="KeyboardMouse", names=("OverrideKey2",), attribute="Key")
_time_selector = RuleSelector(tag="KeyboardMouse", attribute="Time")
_keyboard_mouse_global_selector = RuleSelector(tag="KeyboardMouse", attribute="Key")

KEY_RULE_SPECS: tuple[RuleSpec, ...] = (
    # Keep declaration order: it controls UI field order and validation order.
    RuleSpec(
        "up", 
        source_key="w",
        targets=(_generic_global), 
        selector=_key_selector, 
        unique=True, 
        ui_section=_SECTION_MOVEMENT, 
        ui_label="Up"),
    RuleSpec(
        "down",
        source_key="s",
        targets=(_generic_global),
        selector=_key_selector, 
        unique=True,
        ui_section=_SECTION_MOVEMENT, 
        ui_label="Down"),
    RuleSpec(
        "left", 
        source_key="a",
        targets=(_generic_global), 
        selector=_key_selector, unique=True,
        ui_section=_SECTION_MOVEMENT, 
        ui_label="Left"),
    RuleSpec(
        "right", 
        source_key="d",
        targets=(_generic_global),
        selector=_key_selector,
        unique=True,
        ui_section=_SECTION_MOVEMENT,
        ui_label="Right"),
    RuleSpec(
        "menu_left",
        source_key="q",
        targets=(_menu_left), 
        selector=_key_selector,
        primary_customize_marker=True, 
        ui_section=_SECTION_MENU_NAV,
        ui_label="Menu Left"),
    RuleSpec(
        "menu_right",
        source_key="e", 
        targets=(_menu_right), 
        selector=_key_selector, 
        primary_customize_marker=True,
        ui_section=_SECTION_MENU_NAV, 
        ui_label="Menu Right"),
    RuleSpec(
        "slot1",
        source_key="q",
        targets=(_menu_slots),
        selector=_key_selector,
        ui_section=_SECTION_MENU_ACTION,
        ui_label="Menu 1"),
    RuleSpec(
        "slot2",
        source_key="e",
        targets=(_menu_slots),
        selector=_key_selector,
        ui_section=_SECTION_MENU_ACTION,
        ui_label="Menu 2"),
    RuleSpec("slot3",
        source_key="r",
        targets=(_menu_slots),
        selector=_key_selector,
        ui_section=_SECTION_MENU_ACTION,
        ui_label="Menu 3"),
    RuleSpec("slot4",
        source_key="f",
        targets=(_menu_slots),
        selector=_key_selector,
        ui_section=_SECTION_MENU_ACTION,
        ui_label="Menu 4"),
    RuleSpec("slot5",
        source_key="t",
        targets=(_menu_slots),
        selector=_key_selector,
        ui_section=_SECTION_MENU_ACTION,
        ui_label="Menu 5"),
    RuleSpec("slot6",
        source_key="g",
        targets=(_menu_slots),
        selector=_key_selector,
        ui_section=_SECTION_MENU_ACTION,
        ui_label="Menu 6"),
    RuleSpec("roll_evade_key1",
        targets=(_roll_evade),
        selector=_override_selector_1,
        ui_section=_SECTION_ROLL_EVADE,
        ui_label="Key1",
        ui_width=12),
    RuleSpec("roll_evade_key2",
        targets=(_roll_evade),
        selector=_override_selector_2,
        ui_section=_SECTION_ROLL_EVADE,
        ui_label="Key2",
        ui_width=12),
    RuleSpec("axiom_force_hold_delay",
        targets=(_axiom_timer),
        selector=_time_selector,
        validation=ValidationType.NON_NEGATIVE_FLOAT,
        ui_section="Axiom Force",
        ui_label="Activation Hold Delay (sec, 0 = disable)",
        ui_width=12,
        ui_entry_sticky="w"),
    RuleSpec(
        "enter_game",
        targets=_enter_game_to_menu,
        selector=_keyboard_mouse_global_selector,  # KeyboardMouse only, skips GamePad
        ui_section=_SECTION_ENTER_GAME,
        ui_label="Press to continue / enter game",
        ui_width=12,
        ui_entry_sticky="w"))

@dataclass(frozen=True)
class RebindConfig:
    key_values: dict[str, str]
