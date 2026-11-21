# (r62) keepInventory on in a new world, once: a world where it was turned off later keeps it off.
scoreboard objectives add oror_once dummy
execute unless score #keep_inventory oror_once matches 1 run gamerule keepInventory true
scoreboard players set #keep_inventory oror_once 1
