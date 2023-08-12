# Setup 

## Prerequisites to install

* run ```pip3 install -r requirements.txt```

## Step 1: Create a Discord bot

1. Go to https://discord.com/developers/applications create an application
2. Build a Discord bot under the application
3. Get the token from bot setting

   ![image](https://user-images.githubusercontent.com/89479282/205949161-4b508c6d-19a7-49b6-b8ed-7525ddbef430.png)
4. Store the token to `config.ini` under `discord_bot_token`

   <img height="190" width="390" alt="image" src="https://user-images.githubusercontent.com/89479282/222661803-a7537ca7-88ae-4e66-9bec-384f3e83e6bd.png">

5. Turn MESSAGE CONTENT INTENT `ON`

   ![image](https://user-images.githubusercontent.com/89479282/205949323-4354bd7d-9bb9-4f4b-a87e-deb9933a89b5.png)

6. Invite your bot to your server via OAuth2 URL Generator

   ![image](https://user-images.githubusercontent.com/89479282/205949600-0c7ddb40-7e82-47a0-b59a-b089f929d177.png)

## Authentication
1. Visit https://bard.google.com/
2. F12 for console
3. Session: Application → Cookies → Copy the value of  `__Secure-1PSID` cookie.

## Step 3: Run the bot on the desktop

1. Open a terminal or command prompt

2. Navigate to the directory where you installed the Bard Discord bot

3. Run `python3 main.py` or `python main.py` to start the bot

## Step 4. Invite the bot
![image](https://user-images.githubusercontent.com/91066601/236673317-64a1789c-f6b1-48d7-ba1b-dbb18e7d802a.png)

## Commands

* `/help`: Displays a list of all available commands
* `/chat`: Chat with Bard
* `/reset`: Reset bot's context
* `/public`: Toggle if bot should respond to all messages in chat
* `/private`: Toggle if bot should only respond to /chat
* `/images`: Toggle if bot should respond with images
* `/author`: Provide information about the author
* `/ascii`: Generate ASCII art from text

## Credits

Some of this README.md is from [Zero6992](https://github.com/zero6992)
Codebase is from [armintum](https://github.com/armintum)

