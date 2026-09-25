import Lake
open Lake DSL

package CPOGMain

lean_lib CPOGTheory
lean_lib CPOGCheck
lean_lib CPOGGeneral

@[default_target]
lean_lib CPOGMain
