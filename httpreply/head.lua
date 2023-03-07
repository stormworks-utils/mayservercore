function httpReply(port, request, reply)
    request=mschttp.from_json(request)
    reply=mschttp.from_json(reply)
    module=request['module']
    if false then