import Lake
open Lake DSL

package CPOG

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "v4.34.0"

@[default_target]
lean_lib CPOG
