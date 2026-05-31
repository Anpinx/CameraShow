"""SDK base types and abstract interfaces."""


class BaseAdapter:
    """Common adapter lifecycle."""

    def initialize(self) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        raise NotImplementedError

    @property
    def is_ready(self) -> bool:
        raise NotImplementedError
