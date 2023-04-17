import os
from pathlib import Path
import serverutils

import generator
print(generator.generate(Path("test"), extract=False, http_port=1000, update=False))
serverutils.runserver('msc_test')