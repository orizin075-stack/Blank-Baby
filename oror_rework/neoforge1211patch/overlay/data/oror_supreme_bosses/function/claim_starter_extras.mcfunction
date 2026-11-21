# For players who had the starter kit before r62: run once to get the items r62 added to it.
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s minecraft:iron_sword 1
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s minecraft:shield 1
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s sophisticatedbackpacks:iron_backpack 1
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s minecraft:cooked_beef 32
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s minecraft:torch 32
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s minecraft:iron_pickaxe 1
execute unless entity @s[tag=oror_starter_extras_claimed] run give @s waystones:warp_stone 1
tag @s add oror_starter_extras_claimed
