from __future__ import annotations

from importlib import import_module
from typing import Dict, Type, Union

import yaml

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.utils.file import FORMAT

INCLUDE_TAG = "!INCLUDE"


def depth(d: dict) -> int:
    """
    The depth of a dictionary.

    :param d: The dictionary whose depth to calculate.
    :return: The length of the longest path to a value in the dictionary.
    """
    return (max(map(depth, d.values()), default=0) + 1) if isinstance(d, dict) else 0


def format_to_config(fmt: str) -> Type:
    """
    Maps a CLI format name to its corresponding Config class.

    :param fmt: The format name as known to the CLI.
    :return: The appropriate Config class.
    """
    lookup = {
        FORMAT.fieldtable: "FieldTableConfig",
        FORMAT.ini: "INIConfig",
        FORMAT.nml: "NMLConfig",
        FORMAT.sh: "SHConfig",
        FORMAT.yaml: "YAMLConfig",
    }
    if not fmt in lookup:
        raise log_and_error("Format '%s' should be one of: %s" % (fmt, ", ".join(lookup)))
    cfgclass: Type = getattr(import_module(f"uwtools.config.formats.{fmt}"), lookup[fmt])
    return cfgclass


def log_and_error(msg: str) -> Exception:
    """
    Log an error message and return an exception for the caller to potentially raise.

    :param msg: The error message to log and to associate with raised exception.
    :return: An exception containing the same error message.
    """
    log.error(msg)
    return UWConfigError(msg)


class TaggedString:
    """
    A class supporting custom YAML tags specifying type conversions.

    The constructor implements the interface required by a pyyaml Loader object's add_consructor()
    method. See the pyyaml documentation for details.
    """

    TAGS: Dict[str, type] = {"!float": float, "!int": int}

    def __init__(self, _: yaml.SafeLoader, node: yaml.nodes.ScalarNode) -> None:
        self.tag: str = node.tag
        self.value: str = node.value

    def __repr__(self) -> str:
        return "%s %s" % (self.tag, self.value)

    def convert(self) -> Union[float, int]:
        """
        Return the original YAML value converted to the specified type.

        Will raise an exception if the value cannot be represented as the specified type.
        """
        converters: Dict[str, Union[Type[float], Type[int]]] = dict(zip(self.TAGS, [float, int]))
        return converters[self.tag](self.value)

    @staticmethod
    def represent(dumper: yaml.Dumper, data: TaggedString) -> yaml.nodes.ScalarNode:
        """
        Serialize a tagged scalar as "!type value".

        Implements the interface required by pyyaml's add_representer() function. See the pyyaml
        documentation for details.
        """
        return dumper.represent_scalar(data.tag, data.value)
