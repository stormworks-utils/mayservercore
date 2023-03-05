from pathlib import Path

import generator
generator.generate(Path("test"), extract=False, http_port=1000)
