from app.dispatcher.models.tool import Tool
class ToolRegistry:
    """
    Registry responsável por armazenar
    e localizar ferramentas disponíveis.
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Registra uma nova ferramenta.
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """
        Recupera uma ferramenta pelo nome.
        """
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        """
        Verifica se uma ferramenta existe.
        """
        return name in self._tools

    def list_tools(self) -> list[str]:
        """
        Lista ferramentas disponíveis.
        """
        return list(self._tools.keys())