local zset_key = KEYS[1]

local min_score = tonumber(ARGV[1])
local max_score = tonumber(ARGV[2])
local excluded_user_id = ARGV[3]
local middle_score = (min_score + max_score) / 2

local users = redis.call(
    'ZRANGEBYSCORE',
    zset_key,
    min_score,
    max_score,
    'WITHSCORES'
)

if #users == 0 then
    return nil
end

local closest_user = nil
local closest_diff = math.huge

for i = 1, #users, 2 do
    local user_id = users[i]
    local score = tonumber(users[i + 1])

    if user_id ~= excluded_user_id then
        local diff = math.abs(score - middle_score)
        if diff < closest_diff then
            closest_user = user_id
            closest_diff = diff
        end
    end
end

return closest_user
