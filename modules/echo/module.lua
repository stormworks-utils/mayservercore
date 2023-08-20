function onChatMessage(peerID, name, message)
    server.httpGet('chat',{name=name,message=message})
end

function httpReply()

end