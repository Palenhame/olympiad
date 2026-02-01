local zset_key = KEYS[1]

local user_id_1 = ARGV[1]
local user_id_2 = ARGV[2]

local removed = redis.call(
    'ZREM',
    zset_key,
    user_id_1,
    user_id_2
)


return removed
