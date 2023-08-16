webhook='###CONFIG:webhook:none'
function onChatMessage(peerID, name, message)
    if webhook~='none' then
        server.httpGet('chat',{name=name,message=message,webhook=webhook})
    end
end

function httpReply()

end