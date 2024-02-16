"""Description of the module.

Classes:
    <class>

Functions:
    <function>

Misc. variables:
    <variable>
"""

from jsonschema import validate


class ValidateConfigSchema():
    """Description of the class.

    Args:
        <arg> (<type>): Description of the arg.

    Variables:
        <variable> (<type>): Description of the variable.
    """

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
                "ha_groups",
                "instances"
        ],
        "properties": {
            "ha_groups": {
                "type": "object",
                "items": {
                    "$ref": "#/$defs/ha_group"
                }
            },
            "instances": {
                "type": "object"
            }
        },
        "$defs": {
            "ha_group": {
                "type": "object",
                "required": [
                    "nodes",
                    "restricted",
                    "nofailback",
                    "max_restart",
                    "max_relocate"
                ],
                "properties": {
                    "nodes": {
                        "type": "string",
                        "description": (
                            "Proxmox nodes on which the "
                            "ha group will be applied"
                        )
                    },
                    "restricted": {
                        "type": "boolean",
                        "description": (
                            "Resources bound to restricted groups may "
                            "only run on nodes defined by the group"
                        )
                    },
                    "nofailback": {
                        "type": "boolean",
                        "description": (
                            "The CRM tries to run services on the "
                            "node with the highest priority."
                        )
                    },
                    "max_restart": {
                        "type": "integer",
                        "description": (
                            "Maximal number of tries to restart the service "
                            "on a node after its start failed"
                        ),
                        "minimum": 1
                    },
                    "max_relocate": {
                        "type": "integer",
                        "description": (
                            "Maximal number of service relocate "
                            "tries when a service failes to start"
                        ),
                        "minimum": 1
                    }
                }
            }
        }
    }

    def __init__(self) -> None:
        pass

    def validate(self, data) -> bool:
        """Description of the function/method.

        Parameters:
            <param>: Description of the parameter

        Returns:
            <variable>: Description of the return value
        """
        try:
            validate(
                instance=data,
                schema=self.schema
            )
            return False
        except Exception as e:
            return e

