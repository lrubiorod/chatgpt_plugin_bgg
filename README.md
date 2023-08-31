# ChatGPT BoardGameGeek Plugin

Get a board games assistant ChatGPT plugin using BoardGameGeek information. 
If you do not already have plugin developer access, please [join the waitlist](https://openai.com/waitlist/plugins).

## Setup

To install the required packages for this plugin, run the following command:

```bash
pip install -r requirements.txt
```

To run the plugin, enter the following command:

```bash
python main.py
```

Once the local server is running:

1. Navigate to https://chat.openai.com. 
2. In the Model drop down, select "Plugins" (note, if you don't see it there, you don't have access yet).
3. Select "Plugin store"
4. Select "Develop your own plugin"
5. Enter in `localhost:5003` since this is the URL the server is running on locally, then select "Find manifest file".

The plugin has been successfully installed and activated! To begin, you may pose a question such as, 
"What is the top ten list of trending games on BGG?"

## Data Source and Terms of Use

Please note that all the data utilized in this plugin is sourced from the [BoardGameGeek](https://boardgamegeek.com/) API. 
You should ensure compliance with their [Terms of Use](https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use) 
when using this plugin. It means, due the BGG XMLAPI terms permit use only for non-commercial purposes, the code provided here should only be used locally and strictly without any commercial intentions.




## Getting help

If you run into issues or have questions building a plugin, please join our 
[Developer community forum](https://community.openai.com/c/chat-plugins/20).
