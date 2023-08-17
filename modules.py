from __future__ import annotations

import json
import os
import string

from logger import Logger
import error_handler
import random
from typing import Union
from pathlib import Path
from tumfl import parse, basic_walker, format
from tumfl.Token import Token, TokenType

callbacks: list[str] = [
    "onTick",
    "onCreate",
    "onDestroy",
    "onCustomCommand",
    "onChatMessage",
    "onPlayerJoin",
    "onPlayerSit",
    "onCharacterSit",
    "onCharacterUnsit",
    "onCharacterPickup",
    "onEquipmentPickup",
    "onEquipmentDrop",
    "onCreaturePickup",
    "onPlayerRespawn",
    "onPlayerLeave",
    "onToggleMap",
    "onPlayerDie",
    "onVehicleSpawn",
    "onVehicleLoad",
    "onVehicleUnload",
    "onVehicleTeleport",
    "onVehicleDespawn",
    "onSpawnAddonComponent",
    "onVehicleDamaged",
    "onFireExtinguished",
    "onVehicleUnload",
    "onForestFireSpawned",
    "onForestFireExtinguised",
    "onButtonPress",
    "onObjectLoad",
    "onObjectUnload",
    "onTornado",
    "onMeteor",
    "onTsunami",
    "onWhirlpool",
    "onVolcano",
]
offhandle: list[str] = ["httpReply", "onFirst"]
c_function: list[tuple[str, str]] = [("server", "httpGet")]
SettingsDict = dict[str, Union["SettingsDict", str, int, float, bool]]


def generate(module_name: str, module_path: str, settings: SettingsDict, modules):
    log = Logger("Module proccessor")
    log.info(f'Started generator for module "{module_name}"')
    log.info("Loading layer")
    module_path: Path = Path("modules") / module_path
    try:
        with (module_path / "module.lua").open() as module_fs:
            module_full = module_fs.read()
    except:
        error_handler.handleSkippable(log, f"Unable to fetch module {module_name}")
        return ('',{},{},{},'','','','',)
    try:
        with (module_path / "meta.json").open() as module_meta:
            module_data: dict[str] = json.load(module_meta)
    except:
        error_handler.handleSkippable(log, f"Unable to fetch module data for {module_name}")
        return ('', {}, {}, {}, '', '', '', '',)
    dependencies = module_data.get("dependencies") or []
    incompatibles = module_data.get("incompatibles") or []
    for i in dependencies:
        val, mod = parse_dependency(i, settings)
        if val and (mod not in modules):
            error_handler.handleFatal(
                log,
                f"Module {module_name} has unmet dependencies ({mod})",
            )
    for i in incompatibles:
        val, mod = parse_dependency(i, settings)
        if val and (mod in modules):
            error_handler.handleFatal(
                log,
                f"Module {module_name} is incompatible with another active module ({mod})",
            )

    log.info("Requirements validated")
    # create prefix for private vars/functions to make sure they're not accessible
    prf: str = "".join(random.choices(string.ascii_letters, k=10))
    prefix: str = prf + "_"

    module_id=module_data['id']
    desc=module_data['description']
    log.info("Starting stage two parse")

    chunk = parse(module_full)
    log.info("AST generated")

    generator: Generate = Generate(prefix, module_id.replace(' ','_'), settings)
    generator.visit(chunk)
    log.info(
        f"Processing complete, found {len([i for i in generator.callbacks.values() if i!=[]])} callbacks, "
        f"{len([i for i in generator.functions.values() if i!=[]])} special function calls, "
        f"and {len([i for i in generator.offhandles.values() if i!=[]])} handlers."
    )

    code = format(chunk)
    log.info("Module code generated")
    return (
        code,
        generator.callbacks,
        generator.offhandles,
        generator.functions,
        module_id,
        desc,
        prf,
        module_path,
    )


def parse_dependency(dependency: str, settings: SettingsDict) -> tuple[bool, str]:
    setting, mod, default = dependency.split(":")
    print(f"{setting},{mod},{default}")
    invert = False
    if setting.startswith("!"):
        setting = setting[1:]
        invert = True
    val: bool = bool(fetch_setting(settings, default, setting))
    if invert:
        val = not val
    return val, mod


def fetch_setting(
    settings: SettingsDict, default: str, name: str
) -> bool | int | float | str:
    name_parts: list[str] = name.split(".")
    try:
        setting: SettingsDict | bool | int | float | str = settings
        for i in name_parts:
            assert isinstance(setting, dict), "Invalid setting"
            setting = setting[i]
        value = setting
        assert isinstance(value, (str, int, float, bool)), "Invalid setting"
    except IndexError:
        value = default
    except AssertionError:
        value = default
    except KeyError:
        value = default
    if isinstance(value, str):
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        try:
            value = float(value)
        except ValueError:
            pass
    return value


class Generate(basic_walker.NoneWalker):
    def __init__(self, prefix: str, module_id: str, settings: SettingsDict):
        self.prefix: str = prefix
        self.module_id: str = module_id
        self.settings: SettingsDict = settings
        self.callbacks: dict[str, list[str]] = {name: [] for name in callbacks}
        self.offhandles: dict[str, list[str]] = {name: [] for name in offhandle}
        self.functions: dict[str, list[str]] = {name: [] for _, name in c_function}

    def _get_setting(self, name: str, default: str) -> bool | int | float | str:
        return fetch_setting(self.settings, default, name)

    def visit_Name(self, node: basic_walker.Name) -> None:
        print(node.__dict__)
        print(node.variable_name[:2])
        if node.variable_name[:2] == '__':
            print(node.token.value, 'priv')
            node.variable_name = self.prefix + node.variable_name.replace(' ', '_')
            node.variable_name = node.variable_name[2:].replace(' ','_')
        elif node.variable_name[:1] == '_':
            print(node.variable_name, 'hidd')
            # private var
            node.variable_name = self.module_id + '_' + node.variable_name[1:].replace(' ','_')
        else:
            pass
        print(node.variable_name)

    def visit_String(self, node: basic_walker.String) -> None:
        if node.value.startswith("###CONFIG"):
            parts: list[str] = node.value.split(":")
            setting = self._get_setting(parts[1], parts[2])
            if isinstance(setting, bool):
                token_type: TokenType = TokenType.TRUE if setting else TokenType.FALSE
                new_node = basic_walker.Boolean.from_token(
                    Token(token_type, token_type.value, 0, 0)
                )
                assert node.parent_class
                node.parent_class.replace_child(node, new_node)
            elif isinstance(setting, (int, float)):
                ...
            else:
                node.value = str(setting)

    def visit_FunctionDefinition(self, node: basic_walker.FunctionDefinition) -> None:
        if len(node.names) == 1:
            name: str = node.names[0].variable_name.replace(' ','_')
            prefixed_name: str = name
            if name in callbacks:
                prefixed_name = f"callback_{self.prefix}{name}"
                self.callbacks[name].append(prefixed_name)
            elif name in offhandle:
                prefixed_name = f"offhandle_{self.prefix}{name}"
                self.offhandles[name].append(prefixed_name)
            node.names[0].variable_name = prefixed_name
        super().visit_FunctionDefinition(node)

    def visit_NamedIndex(self, node: basic_walker.NamedIndex) -> None:
        if isinstance(node.lhs, basic_walker.Name):
            index, value = str(node.lhs), str(node.variable_name)
            for a, b in c_function:
                if index == a and value == b:
                    new_name: str = f"mscfunction_{self.prefix}{value}"
                    node.variable_name.variable_name = new_name
                    node.lhs.variable_name = "mschttp"
                    self.functions[value].append(new_name)
        super().visit_NamedIndex(node)

def discover_modules(log):
    paths=next(os.walk('modules'),[None,None])[1]
    if paths==None:
        return {}
    #now have a list of module filepaths
    modules={}
    for i in paths:
        #get modules id
        try:
            with open(f'modules/{i}/meta.json') as metadata:
                module_data=json.load(metadata)
            module_id=module_data['id']
        except:
            log.warn(f"Couldn't find module id for {i}")
            continue
        modules.update({module_id:i})
    return modules