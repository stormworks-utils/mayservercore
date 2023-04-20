function mschttp.NAME(msgtype, data)
    data={['module']='PREFIX',['type']=msgtype,['data']=data}
    json=to_json(data)
    server.httpGet(PORT, "/mschttp?data=" .. escape(json))
end
