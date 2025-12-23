import requests
from apps.social.models import FacebookPage
from .models import Conversation
from .chat_bot import chatbot_reply


def send_message(page_access_token, recipient_id, text):
    
    url = "https://graph.facebook.com/v19.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    params = {"access_token": page_access_token}

    return requests.post(url, json=payload, params=params).json()

def get_page_token_from_db(page_id):
    page = FacebookPage.objects.get(page_id=page_id)
    
    return page


def get_chat_history(external_user_id, social_account):
    try:
        chat = social_account.conversations.get(external_user_id=external_user_id)
    except Conversation.DoesNotExist:
        chat = Conversation.objects.create(
            social_account=social_account,
            external_user_id=external_user_id,
            platform=social_account.platform,
        )
    try:
        history = []
        for message in chat.messages.all():
            history.append({
                "role": message.sender_type,
                "content": message.text
            })
            
        return history, chat
    except:
        return [], chat
    
def store_chat_message(chat, sender_type, text):
    try:
        chat.messages.create(
            sender_type=sender_type,
            text=text
        )
    except Exception as e:
        print(e)
        pass



def handle_message(page_id, sender_id, text):
   
    page = get_page_token_from_db(page_id)
    page_token = page.page_access_token
    social_account = page.social_account
    
    # history, chat = get_chat_history(sender_id, social_account)

    text = text.lower()
    # store_chat_message(chat, "customer", text)
    print('----------------------------')
    reply = chatbot_reply(text, [])
    reply_message = reply.get("reply")
    print(reply_message)
    send_message(page_token, sender_id, reply_message)
    # store_chat_message(chat, "assistant", reply)

    