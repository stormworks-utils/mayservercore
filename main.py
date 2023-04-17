import os
from pathlib import Path
import serverutils

import generator
serverutils.makedir('msc_test')
generator.generate(Path("test"), extract=False, http_port=1000)
#serverutils.update('msc_test')
#serverutils.runserver('msc_test')
