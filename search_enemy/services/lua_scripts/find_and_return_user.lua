local min_score = tonumber(ARGV[1])
local max_score = tonumber(ARGV[2])
local middle_score = (min_score + max_score) / 2
local users = redis.call('ZRANGEBYSCORE', 'users', min_score, max_score, 'WITHSCORES')

if #users > 0 then
    local closest_user = nil
    local closest_diff = math.huge
    for i = 1, #users, 2 do
        local username = users[i]
        local score = tonumber(users[i + 1])
        local diff = math.abs(score - middle_score)
        if diff < closest_diff then
            closest_user = username
            closest_diff = diff
        end
    end
    redis.call('ZREM', 'users', closest_user)
    return closest_user
else
    return nil
end