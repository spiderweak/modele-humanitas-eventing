from typing import Dict
from modules.resource.Application import Application

class VisioConference(Application):
    def __init__(self, data: Dict | None = None, *, id: int | None = None, num_procs: int = 5) -> None:
        super().__init__(data, id=id, num_procs=num_procs)


        # A visio conference has a star topology
        # 5 users