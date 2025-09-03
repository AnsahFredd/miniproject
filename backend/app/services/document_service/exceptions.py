class ContractValidationError(Exception):
    """Custom exception for contract validation failures"""
    def __init__(self, message: str, validation_result: dict):
        self.message = message
        self.validation_result = validation_result
        super().__init__(self.message)
