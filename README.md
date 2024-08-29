# supportiv-chat
Multi-agent interactive support group chat.

## Installation
1. Clone the repository
2. Install the required packages
```bash
pip install -r requirements.txt
```
3. Create a .env file in the root directory and add the following:
```bash
OPENAI_API_KEY="<your_openai_api_key>"
```
4. Run the server
```bash
python app.py
```

## Usage
1. The browser should open automatically when the server is running.
2. Tell supportiv what the issue is you are facing.
Supportiv will generate a support group for you and with other users facing the same issue.
3. Click "Start Meeting" when the description is populated to begin the chat.
4. You can stop the chat at any time by toggling off the "active" switch or
clicking "Start Meeting".
