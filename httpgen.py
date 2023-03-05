base_function='''
function mschttp.NAME(msgtype, data)
    msgtype='PREFIX'+msgtyp
    data={['type']=msgtype,['data']=data}
    json=to_json(data)
    for k, v in pairs(uri_reserved) do
        if string.find(json, k, 0, true) then
            json = string.gsub(json, escape(k), v)
        end
    end
    server.httpGet(PORT, "/mschttp?data=" .. json)
end'''

def generate_http_calls(calls,port):
    string='''
mschttp={}
function mschttp.to_json(value)
    local result = ""
    if type(value) == "table" then
        local is_numeric, last_i = #value > 0, 0
        for i,_ in pairs(value) do
            last_i = last_i + 1
            is_numeric = is_numeric and type(i) == "number" and i == last_i
        end
        if is_numeric then
            for _, v in ipairs(value) do
                result = result .. "," .. to_json(v)
            end
            result = "[" .. result:sub(2,#result) .. "]"
        else
            for k,v in pairs(value) do
                result = result .. "," .. to_json(k) .. ":" .. to_json(v)
            end
            result = "{" .. result:sub(2,#result) .. "}"
        end
    elseif type(value) == "number" then
        result = tostring(value)
    elseif type(value) == "boolean" then
        result = value and "true" or "false"
    else
        result = '"' .. tostring(value) .. '"'
    end
    return result
end
function mschttp.escape(s)
    return (s:gsub("[^%w%d%-%._~]", function(c)
        return string.format("%%%02X", string.byte(c))
    end))
end'''
    for name in calls:
        prefix=name.split('_',1)[1]
        string+=base_function.replace('NAME', name).replace('PREFIX', prefix).replace('PORT', str(port))
        string+='\n'
    return string