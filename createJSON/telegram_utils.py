from telegram import Update

async def send_telegram_message(update: Update, message: str):
    print(f"Sending message: {message}")

async def get_telegram_input(update: Update, prompt: str):
    print(f"Prompting user: {prompt}")
    response = input("Enter your response: ")
    return response
