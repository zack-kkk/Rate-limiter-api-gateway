-- KEYS[1]: Client Identifier (e.g., "rate_limit:127.0.0.1")
-- ARGV[1]: Bucket Capacity (Max Tokens)
-- ARGV[2]: Refill Rate (Tokens per second)
-- ARGV[3]: Current Unix Timestamp
-- ARGV[4]: Tokens requested (default 1)

local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Fetch current state from Redis
local data = redis.call("HMGET", key, "tokens", "last_updated")
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if tokens == nil then
    tokens = capacity
    last_updated = now
else
    -- Compute generated tokens based on elapsed time
    local delta = math.max(0, now - last_updated)
    local tokens_to_add = delta * refill_rate
    tokens = math.min(capacity, tokens + tokens_to_add)
    last_updated = now
end

-- Verify if request can be served
if tokens >= requested then
    tokens = tokens - requested
    redis.call("HMSET", key, "tokens", tokens, "last_updated", last_updated)
    -- Auto-expire key after complete refill to prevent memory leaks
    redis.call("EXPIRE", key, math.ceil(capacity / refill_rate))
    return {1, math.floor(tokens)}
else
    return {0, math.floor(tokens)}
end
