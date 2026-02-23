from application.ports.ai_port import AIPort
from domain.entities.recipe import Recipe


class ImportRecipeUseCase:
    """Parse a recipe from a URL via AI — returns a draft Recipe, not yet persisted."""

    def __init__(self, ai_port: AIPort):
        self._ai_port = ai_port

    async def execute(self, url: str) -> Recipe:
        """
        Returns a Recipe domain object populated from the webpage.
        Raises ValueError if no recipe is found.
        """
        return await self._ai_port.parse_recipe_from_url(url)
