_webhook='###CONFIG:webhook:none'
function onChatMessage(peerID, name, message)
    if _webhook~='none' then
        server.httpGet('chat',{name=name,message=message,webhook=_webhook})
    end
end

function httpReply()

end