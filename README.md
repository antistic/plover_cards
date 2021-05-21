# plover_cards

A Plover plugin which helps you build an Anki deck from the words and phrases you have typed.


![screenshot of card builder window](https://user-images.githubusercontent.com/3298461/112348383-afbd6800-8cbf-11eb-8de7-8b6d48fe85f6.png)

## Setup

- Enable "plover_cards_hook"
  - Right click the Plover icon, "Configure", "Plugins" tab, check the box next to "plover_cards_hook", "Apply"
- Install [Anki](https://apps.ankiweb.net/)
- Make sure all your steno cards are under the same [note type](https://docs.ankiweb.net/getting-started.html?highlight=note%20type#note-types), and you don't have any non-steno cards under that note type

## Plover Cards Hook

This part of the plugin listens to what you write and records the suggestions (you don't need to have the suggestion window open). It'll keep a count of how many times you use a stroke so you can focus on only the words you use often (or least often). Unlike the suggestions window, it'll also record suggestions for command, prefix and suffix strokes if you use them.

The data is stored in `{your_plover_config_folder}/plover_cards/card_suggestions.pickle`. This gets saved when you disable the extension, quit Plover and every 5 minutes.

## Card Builder

This is where you can look at the suggestions and choose which ones to export as a csv. It'll ignore any suggestions for words/phrases you already have in Anki, or previously added to the ignore file.

### Usage

- Make sure Anki isn't already running
- (from the menu) Right click the Plover icon, "Tools", "Card Builder"
- (from the gui) Click "Card Builder" icon in the top bar of the main Plover window.

### Set Options

| Option                            | What it's used for                                                                                                                                                                                                  |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Anki Collection                   | The Anki collection with existing cards, which will be ignored when building cards. Defaults to the first `.anki2` file it can find in the [default Anki  path](https://apps.ankiweb.net/docs/manual20.html#files). |
| Note Type                         | The note type for existing cards, which will be ignored when building cards. Defaults to "Basic".                                                                                                                   |
| Ignore File                       | Where to save the list of words to ignore. Defaults to `{your_plover_config_folder}/plover_cards/ignore.txt`.                                                                                                       |
| Output File                       | Where to save the CSV file of new cards, which can then be imported into Anki. Defaults to `{your_plover_config_folder}/plover_cards/new_notes.txt`.                                                                |
| Clear output file before starting | Clear the output file when you press start. You'll want this on if you have imported the cards from the previous session, and off if you're continuing the previous session.                                        |

These options are saved in `{your_plover_config_folder}/plover_cards.cfg`

### Build Cards

- *Stroke list*: Pick which stroke you want on the back of the Anki card here.
- *Card list*:
  - You can click on any of the following columns to sort by that column. Click again to change the sort order.
  - *Count*: The number of times you typed this word and/or the number of times it was suggested to you.
  - *Count (shorter)*: The number of times the program found a shorter suggestion for what you typed
  - *Last Used*: The date and time you last used this word.
  - *Translation*: The word or phrase on the front of the Anki card.
  - *Stroke*: The stroke on the back of the Anki card.
  - *Similar ignored*: Similar words that are either already in the Anki deck or have been added to the ignore list.
- *Buttons*:
  - **Clear**: Clear the chosen stroke. Useful if you want to skip this card, since by default it will choose the first stroke in the list.
  - **Ignore**: Add this word/phrase to the ignore list. It won't appear next time you use the card builder.
  - **<**: Go to previous card.
  - **>**: Go to next card.
  - **Finish**: Finish building cards.

### Add to Anki

In Anki go to `File` then `Import`. Select the output file you chose at the beginning (defaults to `{your_plover_config_folder}/plover_cards/new_notes.txt`).
