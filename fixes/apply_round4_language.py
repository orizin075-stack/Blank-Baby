from pathlib import Path
p = Path("CPOG_ProofComplete_v50/CPOG/Language.lean")
s = p.read_text()
s = s.replace("import Std\nimport CPOG.Main\nimport CPOG.Theory\nimport CPOG.Origin", "import CPOG.Main")
p.write_text(s)
