class DispatcherError(Exception):
    """
    Erro base do Dispatcher.
    """
    pass


class ToolNotFoundError(DispatcherError):
    """
    Ferramenta solicitada não existe no registry.
    """
    pass


class ToolExecutionError(DispatcherError):
    """
    A ferramenta existe, mas falhou durante execução.
    """
    pass


class InvalidToolRequestError(DispatcherError):
    """
    Request recebido não é válido.
    """
    pass