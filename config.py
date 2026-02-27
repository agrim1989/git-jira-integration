class MCPConfig:
    def __init__(self, network_settings: dict, security_protocols: dict, storage_allocations: dict):
        self.network_settings = network_settings
        self.security_protocols = security_protocols
        self.storage_allocations = storage_allocations

    def validate_config(self) -> bool:
        # Add validation logic here
        return True
