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
end